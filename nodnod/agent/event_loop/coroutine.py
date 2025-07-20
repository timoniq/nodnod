import typing
import asyncio
from nodnod.compose import compose_node
from nodnod.node import Node
from nodnod.scope import Scope
import fntypes
from nodnod.box import Box
from nodnod.error import NodeError

type DependencyFuture[T] = asyncio.Future[fntypes.Result[Box[T], NodeError]]
type Pusher = typing.Callable[[dict[type[Node], asyncio.Future], type[Node]], None]


async def compose_coroutine(
    node: type[Node],
    scope: Scope,
    dependencies: list[DependencyFuture],
):
    await asyncio.gather(*dependencies)

    return await compose_node(node, scope)


async def dependency_sequential_either_coroutine(
    first_dependency: DependencyFuture,
    other_dependencies: tuple[type[Node], ...],
    futures: dict[type[Node], asyncio.Future],
    pusher: Pusher,
) -> fntypes.Result[Box[typing.Any], NodeError]:
    """
    How sequential either is getting resolved:

    SequentialEither[A, B, C]
       `A` already has an active future
       If future's result is composition failure
       we start pushing new dependencies one by one
       into the concurrent pool and returning the
       positive result if we have one
    """

    if result := await first_dependency:
        return result
    
    for dep in other_dependencies:
        if existing_future := futures.get(dep):
            if result := await existing_future:
                return result
            continue

        pusher(futures, dep)
        if result := await futures[dep]:
            return result
    
    return fntypes.Error(NodeError("No node found"))


async def dependency_concurrent_either_corountine(
    dependencies: list[DependencyFuture],
) -> fntypes.Result[Box[typing.Any], NodeError]:
    done, pending = await asyncio.wait(
        dependencies,
        return_when=asyncio.FIRST_COMPLETED,
    )
    return await done.pop()
