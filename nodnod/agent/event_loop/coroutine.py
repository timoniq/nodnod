import typing
import asyncio
from nodnod.compose import compose_node
from nodnod.node import Node
from nodnod.scope import Scope
import fntypes
from nodnod.value import Value
from nodnod.error import NodeError
from nodnod.interface.result_node import ResultNode

type DependencyFuture[T] = asyncio.Future[fntypes.Result[Value[T], NodeError]]
type Pusher = typing.Callable[[dict[type[Node], asyncio.Future], type[Node]], None]


async def compose_coroutine(
    node: type[Node],
    node_scope: Scope,
    local_scope: Scope,
    dependencies: list[DependencyFuture],
) -> fntypes.Result[Value[typing.Any], NodeError]:
    for result in await asyncio.gather(*dependencies):
        if fntypes.is_err(result):
            return fntypes.Error(NodeError(f"could not resolve dependencies of {node.__name__}", from_error=result.error))

    return await compose_node(node, node_scope, local_scope)


async def result_node_compose_coroutine(
    node: type[ResultNode],
    node_scope: Scope,
    from_node: DependencyFuture,
) -> fntypes.Result[Value[typing.Any], NodeError]:
    result = (await asyncio.gather(from_node, return_exceptions=True))[0]

    if isinstance(result, BaseException):
        if not node.__compose__(result):
            raise result
        value = Value(node.__type__, fntypes.Error(result))
    elif fntypes.is_err(result):
        if not node.__compose__(result.error):
            raise result.error
        value = Value(node.__type__, result)
    else:
        value = Value(node.__type__, fntypes.Ok(result.value.value))

    node_scope[node] = value
    return fntypes.Ok(value)
    

async def dependency_sequential_either_coroutine(
    first_dependency: tuple[type[Node], DependencyFuture],
    other_dependencies: tuple[type[Node], ...],
    futures: dict[type[Node], asyncio.Future],
    pusher: Pusher,
    mapped_scopes: dict[type[Node], Scope],
    local_scope: Scope,
) -> fntypes.Result[Value[typing.Any], NodeError]:
    """
    How sequential either is getting resolved:

    SequentialEither[A, B, C]
       `A` already has an active future
       If future's result is composition failure
       we start pushing new dependencies one by one
       into the is_concurrent pool and returning the
       positive result if we have one
    """

    first_dependency_node, first_dependency_future = first_dependency
    errors: list[NodeError] = []

    result = await first_dependency_future
    if result:
        scope = mapped_scopes.get(first_dependency_node, local_scope)
        scope[first_dependency_node] = result.unwrap()
        return result
    else:
        errors.append(result.error)
    
    for dep in other_dependencies:
        if existing_future := futures.get(dep):
            result = await existing_future
            if result:
                return result
            errors.append(result.error)
            continue

        pusher(futures, dep)
        result = await futures[dep]
        if result:
            scope = mapped_scopes.get(dep, local_scope)
            scope[dep] = result.unwrap()
            return result
        errors.append(result.error)
    
    return fntypes.Error(NodeError("no option found for either", from_many=errors))


async def dependency_concurrent_either_corountine(
    dependencies: list[DependencyFuture],
) -> fntypes.Result[Value[typing.Any], NodeError]:
    errors: list[NodeError] = []

    candidate_dependencies = set(dependencies)
    while candidate_dependencies:
        done, pending = await asyncio.wait(
            dependencies,
            return_when=asyncio.FIRST_COMPLETED,
        )
        for ready_result_future in done:
            result = await ready_result_future
            if result:
                return result
            errors.append(result.error)
        candidate_dependencies = pending

    return fntypes.Error(NodeError("no option found for either", from_many=errors))
