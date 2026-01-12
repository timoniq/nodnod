import asyncio
import typing

import kungfu

from nodnod.compose import compose_node
from nodnod.error import NodeError
from nodnod.scope import Scope
from nodnod.value import Value

if typing.TYPE_CHECKING:
    from nodnod.interface.result_node import ResultNode
    from nodnod.node import Node

type DependencyFuture[T] = asyncio.Future[kungfu.Result[Value[T], NodeError]]
type Pusher = typing.Callable[[dict[type["Node"], asyncio.Future], type["Node"]], None]


async def compose_coroutine(
    node: type["Node"],
    node_scope: Scope,
    local_scope: Scope,
    dependencies: list[DependencyFuture],
) -> kungfu.Result[Value[typing.Any], NodeError]:
    for result in await asyncio.gather(*dependencies):
        if kungfu.is_err(result):
            return kungfu.Error(NodeError(f"could not resolve dependencies of `{node.__name__}`", from_error=result.error))

    return await compose_node(node, node_scope, local_scope)


async def result_node_compose_coroutine(
    node: type["ResultNode[typing.Any, typing.Any]"],
    node_scope: Scope,
    from_node: DependencyFuture,
) -> kungfu.Result[Value[typing.Any], NodeError]:
    result = (await asyncio.gather(from_node, return_exceptions=True))[0]

    if isinstance(result, BaseException):
        if not node.__compose__(result):
            raise result
        value = Value(node.__type__, kungfu.Error(result))
    elif kungfu.is_err(result):
        if not node.__compose__(result.error):
            raise result.error
        value = Value(node.__type__, result)
    else:
        value = Value(node.__type__, kungfu.Ok(result.value.value))

    node_scope[node] = value
    return kungfu.Ok(value)


async def dependency_sequential_either_coroutine(
    first_dependency: tuple[type["Node"], DependencyFuture],
    other_dependencies: tuple[type["Node"], ...],
    futures: dict[type["Node"], asyncio.Future],
    pusher: Pusher,
    mapped_scopes: dict[type["Node"], Scope],
    local_scope: Scope,
) -> kungfu.Result[Value, NodeError]:
    """How sequential either is getting resolved:

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

    return kungfu.Error(NodeError("no option found for either", from_many=errors))


async def dependency_concurrent_either_coroutine(
    dependencies: list[DependencyFuture],
) -> kungfu.Result[Value, NodeError]:
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

    return kungfu.Error(NodeError("no option found for either", from_many=errors))


__all__ = (
    "compose_coroutine",
    "dependency_concurrent_either_coroutine",
    "dependency_sequential_either_coroutine",
    "result_node_compose_coroutine",
)
