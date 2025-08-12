import typing

from nodnod.utils.create_node import create_node_from_composable

if typing.TYPE_CHECKING:
    from nodnod.interface.composable import Composable

GENERIC_MARK: typing.Final = "is_generic"


def is_generic_node(obj: typing.Any, /) -> bool:
    return getattr(obj, GENERIC_MARK, False) is True


class generic_node:  # noqa: N801
    def __new__[T: Composable](cls, composable: type[T], /) -> type[T]:
        node_class = create_node_from_composable(composable, namespace={GENERIC_MARK: True})
        setattr(node_class, GENERIC_MARK, True)
        return node_class  # type: ignore


__all__ = ("generic_node", "is_generic_node")
