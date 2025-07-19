from nodnod.node import Node
from nodnod.box import Box
from nodnod.utils.aio import awaitable_noop
import typing
import fntypes
import asyncio
from collections import OrderedDict


class Scope(OrderedDict[type[Node[typing.Any]], Node[typing.Any]]):
    def __init__(self, prev: "Scope | None" = None):
        self.prev = prev
    
    def retrieve[T](self, key: type[Node[T]]) -> fntypes.Option[Node[T]]:
        if key not in self:
            if not self.prev:
                return fntypes.Nothing()
            return self.prev.retrieve(key)
        return fntypes.Some(self[key])
    
    def __repr__(self) -> str:
        return ", ".join(f"{node_t.__name__}: {node.value}" for node_t, node in self.items())
    
    def close(self) -> typing.Awaitable[typing.Any]:
        coros = []

        while self:
            _, node = self.popitem()
            result = node.close()
            if not isinstance(result, awaitable_noop):
                coros.append(result)
        
        if not coros:
            return awaitable_noop()
        
        return asyncio.gather(*coros)

