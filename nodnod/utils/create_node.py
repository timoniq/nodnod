from __future__ import annotations

import types
import typing

if typing.TYPE_CHECKING:
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


__all__ = ("create_node",)
