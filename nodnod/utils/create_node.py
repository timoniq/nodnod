from __future__ import annotations

import types
import typing
from functools import cache

from nodnod.error import NodeBuildError

if typing.TYPE_CHECKING:
    from nodnod.interface.composable import Composable
    from nodnod.node import Node


def create_node[T: Node](
    name: str,
    base_node: type[T],
    bases: tuple[typing.Any, ...],
    namespace: dict[str, typing.Any],
    **kwds: typing.Any,
) -> type[T]:
    return type(
        name,
        types.resolve_bases((*bases, base_node)),
        namespace,
        **kwds,
    )


@cache
def _create_node_from_composable[T](composable: type[Composable[T]]) -> type[Node[T]]:
    from nodnod.node import Node

    return create_node(
        name=f"Node:{composable.__name__}",
        base_node=Node,
        bases=(composable,),
        namespace=dict(
            __type__=composable,
            __compose__=composable.__compose__,
            __module__=composable.__module__,
        ),
    )


def create_node_from_composable[T](composable: type[Composable[T]], /) -> type[Node[T]]:
    composable = typing.get_origin(composable) or composable

    if not hasattr(composable, "__compose__"):
        raise NodeBuildError(f"`{composable.__name__}` does not have a `__compose__` method.")

    return _create_node_from_composable(typing.get_origin(composable) or composable)


__all__ = ("create_node", "create_node_from_composable")
