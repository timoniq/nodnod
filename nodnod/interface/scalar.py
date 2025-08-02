import types
import typing

from nodnod.node import Node

type Generator[T] = typing.Generator[typing.Any, typing.Any, T] | typing.AsyncGenerator[T, typing.Any]


class Composable[T](typing.Protocol):
    @classmethod
    def __compose__(cls, *args, **kwargs) -> T:
        ...


class scalar_node[T]:  # noqa: N801
    @typing.overload
    def __new__(cls, x: Composable[typing.Awaitable[T]], /) -> type[T]: ...

    @typing.overload
    def __new__(cls, x: Composable[Generator[T]], /) -> type[T]: ...

    @typing.overload
    def __new__(cls, x: Composable[T], /) -> type[T]: ...

    @typing.overload
    def __new__(cls, x: T, /) -> type[T]: ...

    def __new__(cls, node_class: typing.Any, /) -> typing.Any:
        bases = [node_class]
        node_namespace = dict(is_scalar=True, __module__=node_class.__module__)

        if not any(issubclass(base, Node) for base in types.resolve_bases(bases) if isinstance(base, type)):
            bases.append(Node)

        return type(node_class.__name__, tuple(types.resolve_bases(bases)), node_namespace)


__all__ = ("scalar_node",)

