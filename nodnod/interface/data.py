import typing

from nodnod.node import ComposeResponse, Node


@typing.dataclass_transform()
class DataNode(Node[typing.Any], abstract=True):
    @classmethod
    def __compose__(cls, *args: typing.Any, **kwargs: typing.Any) -> ComposeResponse[typing.Self]:
        ...


__all__ = ("DataNode",)
