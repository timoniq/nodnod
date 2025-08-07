from nodnod.node import Node
from nodnod.compose import ComposeResponse
import fntypes
import typing


class Either(Node[fntypes.Variative], abstract=True):
    concurrent: bool
    __either__: tuple[type[Node], ...]

    def __init__(self, value: typing.Any):
        self.value = value
    
    @classmethod
    def __compose__(cls, node: fntypes.Variative):
        return cls(node.v.value)
    
    @classmethod
    def __bound_compose__(cls, nodes: set[Node]) -> ComposeResponse:
        node = nodes.copy().pop()
        return cls.__compose__(fntypes.Variative(node))
    
    def __init_subclass__(cls, abstract: bool = False) -> None:
        if not abstract:
            if cls.concurrent:
                # All nodes are listed as linked for concurrent (racing) disjunction
                cls.__dependencies__ = set(cls.__either__)
            else:
                # Only first node must be resolved to make the first check.
                # The next nodes will be set as dependency sequentially
                cls.__dependencies__ = {cls.__either__[0]}


class SequentialEither(Either, abstract=True):
    concurrent = False


class ConcurrentEither(Either, abstract=True):
    concurrent = True
