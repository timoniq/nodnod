import typing

from nodnod.node import ComposeResponse, Node


@typing.dataclass_transform()
class DataNode(Node, abstract=True):
    @classmethod
    def __compose__(cls, *args: typing.Any, **kwargs: typing.Any) -> ComposeResponse[typing.Any]: ...


__all__ = ("DataNode",)
