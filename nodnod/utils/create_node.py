from __future__ import annotations

import types
import typing

if typing.TYPE_CHECKING:
    from nodnod.interface.composable import Composable
    from nodnod.node import ComposeResponse, Node


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


def create_node_from_composable[T: Composable](
    composable: type[T],
    name: str | None = None,
    namespace: dict[str, typing.Any] | None = None,
    bases: tuple[typing.Any, ...] = (),
    **kwds: typing.Any,
) -> type[Node]:
    from nodnod.node import Node

    if issubclass(composable, Node):
        return composable

    return create_node(
        name=name or composable.__name__,
        base_node=Node,
        bases=bases,
        namespace=composable.__dict__ | dict(
            __compose__=composable.__dict__["__compose__"],  # get as classmethod with __compose__ signature
            __dependencies__=getattr(composable, "__dependencies__", None),
            __injections__=getattr(composable, "__injections__", None),
            __type__=getattr(composable, "__type__", None),
            __initialize__=composable.__dict__.get("__initialize__", None),
            __module__=composable.__module__,
            **(namespace or {}),
        ),
        **kwds,
    )


def create_node_from_compose_function[T](
    compose_function: typing.Callable[..., ComposeResponse[T]],
    name: str | None = None,
    namespace: dict[str, typing.Any] | None = None,
    bases: tuple[typing.Any, ...] = (),
    **kwds: typing.Any,
) -> type[Node[T]]:
    from nodnod.node import Node

    return create_node(
        name=name or "".join(x.title() for x in compose_function.__name__.split("_")),
        base_node=Node,
        bases=bases,
        namespace=dict(
            __compose__=compose_function,
            __module__=compose_function.__module__,
            **(namespace or {}),
        ),
        **kwds,
    )


__all__ = (
    "create_node",
    "create_node_from_composable",
    "create_node_from_compose_function",
)
