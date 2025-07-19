from nodnod.box import Box
from nodnod.utils import awaitable_noop, generator_asend, generator_send
import typing
import types


type Generator[T] = typing.Generator[T, None, None] | typing.AsyncGenerator[T, None]
type ComposeResponse[T] = T | typing.Awaitable[T] | Generator[T]


class Node[T]:
    __dependencies__: set[type["Node"]] = set()

    def __init__(self, value: T, generator: Generator[T] | None = None):
        self.value = value
        self.generator = generator
    
    @classmethod
    def __compose__(cls, *args, **kwargs) -> ComposeResponse[T]:
        ...
    
    def __box__(self) -> Box[T]:
        return Box(self.value)
    
    def __repr__(self) -> str:
        return f"<node {self.__class__.__name__} = {self.value}>"


    def close(self) -> typing.Awaitable[typing.Any]:
        if self.generator is None:
            return awaitable_noop()
        
        if isinstance(self.generator, types.AsyncGeneratorType):
            return generator_asend(self.generator)
        
        elif isinstance(self.generator, types.GeneratorType):
            generator_send(self.generator)
        
        return awaitable_noop()


type Queue = set[type[Node]]
