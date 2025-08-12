from __future__ import annotations

import inspect
import typing

from nodnod.error import NodeBuildError
from nodnod.utils.create_node import create_node_from_composable, create_node_from_compose_function

if typing.TYPE_CHECKING:
    import types

    from nodnod.interface.composable import Composable
    from nodnod.node import Generator

    class NodeComposeFunction[R](typing.Protocol):
        __name__: str
        __code__: types.CodeType

        def __call__(self, *args: typing.Any, **kwargs: typing.Any) -> R: ...


SCALAR_MARK: typing.Final = "is_scalar"


def is_scalar(obj: typing.Any, /) -> bool:
    return getattr(obj, SCALAR_MARK, False) is True


class scalar_node[T]:  # noqa: N801
    @typing.overload
    def __new__(cls, x: NodeComposeFunction[Composable[typing.Awaitable[T]]], /) -> type[T]: ...

    @typing.overload
    def __new__(cls, x: NodeComposeFunction[Composable[Generator[T]]], /) -> type[T]: ...

    @typing.overload
    def __new__(cls, x: NodeComposeFunction[Composable[T]], /) -> type[T]: ...

    @typing.overload
    def __new__(cls, x: NodeComposeFunction[T], /) -> type[T]: ...

    def __new__(cls, x: typing.Any, /) -> type[typing.Any]:
        if inspect.isfunction(x):
            node_class = create_node_from_compose_function(x)
        elif hasattr(x, "__compose__"):
            node_class = create_node_from_composable(x)
        else:
            raise NodeBuildError(
                f"Cannot create scalar node from `{x!r}`, only functions and composable classes are supported.",
            )

        setattr(node_class, SCALAR_MARK, True)
        return node_class


__all__ = ("scalar_node", "is_scalar")
