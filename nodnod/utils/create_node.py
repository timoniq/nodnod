from __future__ import annotations

import types
import typing
from contextvars import ContextVar

if typing.TYPE_CHECKING:
    from nodnod.interface.composable import Composable
    from nodnod.node import Node

COMPOSABLE_NODES: typing.Final = ContextVar("COMPOSABLE_NODES", default={})


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


def create_node_from_composable(composable: type[Composable]) -> type[Node]:
    composable = typing.get_origin(composable) or composable
    composable_nodes = COMPOSABLE_NODES.get()

    if (node := composable_nodes.get(composable)) is not None:
        return node

    from nodnod.node import Node

    node = create_node(
        name=f"Node:{composable.__name__}",
        base_node=Node,
        bases=(),
        namespace=dict(
            __type__=composable,
            __compose__=composable.__compose__,
            __module__=composable.__module__,
        ),
    )
    return composable_nodes.setdefault(composable, node)


__all__ = (
    "create_node",
    "create_node_from_composable",
)
