from nodnod.node import Generator, Node
from nodnod.utils.generator import generator_asend, generator_send
from nodnod.utils.aio import awaitable_noop
import types
import typing


class Value[T]:
    def __init__(self, node_cls: type[Node], value: T, generator: Generator[T] | None = None):
        self.node_cls = node_cls
        self.value = value
        self.generator = generator

    def __unbox__(self) -> T:
        return self.value
    
    def close(self) -> typing.Awaitable[typing.Any]:
        if self.generator is None:
            return awaitable_noop()
        
        if isinstance(self.generator, types.AsyncGeneratorType):
            result = generator_asend(self.generator)
            self.generator = None
            return result
        
        elif isinstance(self.generator, types.GeneratorType):
            generator_send(self.generator)
        
        self.generator = None
        return awaitable_noop()
    
    def __repr__(self) -> str:
        return f"<value of {self.node_cls.__name__} = {self.value}{'' if self.generator is None else ' (open generator)'}>"
