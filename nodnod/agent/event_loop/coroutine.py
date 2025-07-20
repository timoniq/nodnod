import typing
import asyncio
from nodnod.composer import compose_node
from nodnod.node import Node
from nodnod.scope import Scope
import fntypes
from nodnod.box import Box
from nodnod.error import NodeError

type DependencyFuture[T] = asyncio.Future[fntypes.Result[Box[T], NodeError]]


async def compose_coroutine(
    node: type[Node],
    scope: Scope,
    dependencies: list[DependencyFuture],
):
    await asyncio.gather(*dependencies)

    return await compose_node(node, scope)


async def dependency_either_coroutine(
    dependencies: list[DependencyFuture],
) -> fntypes.Result[Box[typing.Any], NodeError]:
    for dependency in dependencies:
        if result := await dependency:
            return result
    
    return fntypes.Error(NodeError("No node found"))


async def dependency_parallel_either_corountine(
    dependencies: list[DependencyFuture],
) -> fntypes.Result[Box[typing.Any], NodeError]:
    done, pending = await asyncio.wait(
        dependencies,
        return_when=asyncio.FIRST_COMPLETED,
    )
    return await done.pop()
