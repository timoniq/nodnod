from nodnod.node import Node
from nodnod.box import Box
import typing
import fntypes


class Scope(dict[type[Node[typing.Any]], Node[typing.Any]]):
    def __init__(self, prev: "Scope | None" = None):
        self.prev = prev
    
    def retrieve[T](self, key: type[Node[T]]) -> fntypes.Option[Box[T]]:
        if key not in self:
            if not self.prev:
                return fntypes.Nothing()
            return self.prev.retrieve(key)
        return fntypes.Some(self[key].__box__())
    
    def __repr__(self) -> str:
        return ", ".join(f"{node_t.__name__}: {node.value}" for node_t, node in self.items())
