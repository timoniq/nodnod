import typing

from nodnod import Node, Value


class NodeConstructor(Node, abstract=True):
    @classmethod
    def __construct__(cls, *args: typing.Any) -> typing.Self:
        raise NotImplementedError

    def __class_getitem__(cls, item: typing.Any | tuple[typing.Any, ...], /) -> typing.Any:
        data = cls.__construct__(*((item,) if not isinstance(item, tuple) else item))
        node = type(cls.__name__, (cls,), {"__module__": cls.__module__, "__injections__": set(cls.__injections__ ^ {typing.Self})})
        setattr(
            node,
            "__initialize__",
            lambda values: cls.__initialize__({*values, Value(typing.Self, data)}),  # type: ignore
        )
        setattr(node, "__type__", node)
        return node


__all__ = ("NodeConstructor",)
