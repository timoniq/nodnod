from __future__ import annotations

import types
import typing
from functools import cache

if typing.TYPE_CHECKING:
    from nodnod.interface.composable import Composable
    from nodnod.node import Node


def create_node[T: Node[typing.Any]](
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
def create_node_from_composable(composable: type[Composable]) -> type[Node[typing.Any, typing.Any]]:
    from nodnod.node import Node

    return create_node(
        name=f"Node:{composable.__name__}",
        base_node=Node,
        bases=(),
        namespace=dict(
            __type__=composable,
            __compose__=composable.__compose__,
            __module__=composable.__module__,
        ),
    )


__all__ = (
    "create_node",
    "create_node_from_composable",
)
