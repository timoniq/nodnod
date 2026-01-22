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
        if isinstance(node_class, type):
            if not any(issubclass(base, Node) for base in node_class.mro()):
                return create_node(
                    name=node_class.__name__,
                    base_node=Node,
                    bases=(node_class,),
                    namespace=dict(is_scalar=True, __module__=node_class.__module__),
                )

            node_class.is_scalar = True
            return node_class

        if callable(node_class):
            return type(
                f"ScalarNode:{node_class.__name__}",
                (Node,),
                dict(__compose__=node_class, __module__=node_class.__module__, is_scalar=True),
            )

        raise TypeError(f"scalar_node must be kind of class or function, got `{type(node_class)}`.")


__all__ = ("scalar_node",)
