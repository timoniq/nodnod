import typing

import kungfu

from nodnod.compose import ComposeResponse
from nodnod.error import NodeError
from nodnod.node import Node
from nodnod.value import Value


class Either(Node[kungfu.Sum], abstract=True):
    is_concurrent: bool
    is_scalar: bool = False

    __either__: tuple[type[Node], ...]

    def __init__(self, value: typing.Any) -> None:
        self.value = value

    @classmethod
    def __compose__(cls, node_value: Value) -> typing.Any:
        value = node_value.unbox()
        return value if cls.is_scalar else cls(value)

    @classmethod
    def __initialize__(cls, values: set[Value]) -> ComposeResponse:
        return cls.__compose__(next(iter(values)))

    def __init_subclass__(cls, abstract: bool = False) -> None:
        if not abstract:
            if cls.is_concurrent:
                # All nodes are listed as linked for is_concurrent (racing) disjunction
                cls.__dependencies__ = set(cls.__either__)
            else:
                # Only first node must be resolved to make the first check.
                # The next nodes will be set as dependency sequentially
                cls.__dependencies__ = {cls.__either__[0]}

            cls.__injections__ = set()
            cls.__type__ = cls.__type__ or cls


class SequentialEither(Either, abstract=True):
    is_concurrent = False


class ConcurrentEither(Either, abstract=True):
    is_concurrent = True


__all__ = ("ConcurrentEither", "Either", "SequentialEither")
