import inspect
import typing

from nodnod.interface.composable import Composable
from nodnod.node import Node
from nodnod.utils.create_node import create_node

type Generator[T] = typing.Generator[T, typing.Any, typing.Any] | typing.AsyncGenerator[T, typing.Any]


class scalar_node[T]:  # noqa: N801
    @typing.overload
    def __new__(cls, x: Composable[typing.Awaitable[T]], /) -> type[T]: ...

    @typing.overload
    def __new__(cls, x: Composable[Generator[T]], /) -> type[T]: ...

    @typing.overload
    def __new__(cls, x: Composable[T], /) -> type[T]: ...

    @typing.overload
    def __new__(cls, x: typing.Callable[..., typing.Awaitable[T]], /) -> type[T]: ...

    @typing.overload
    def __new__(cls, x: typing.Callable[..., Generator[T]], /) -> type[T]: ...

    @typing.overload
    def __new__(cls, x: typing.Callable[..., T], /) -> type[T]: ...

    @typing.overload
    def __new__(cls, x: T, /) -> type[T]: ...

    def __new__(cls, node_class: typing.Any, /) -> typing.Any:
        if inspect.isfunction(node_class):
            node_class = type(node_class.__name__, (), dict(__compose__=node_class))

        if not any(issubclass(base, Node) for base in node_class.__bases__):
            return create_node(
                name=node_class.__name__,
                base_node=Node,
                bases=(node_class,),
                namespace=dict(is_scalar=True, __module__=node_class.__module__),
            )

        node_class.is_scalar = True
        return node_class


__all__ = ("scalar_node",)
