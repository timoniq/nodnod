from nodnod.node import Generator
from nodnod.utils.generator import generator_asend, generator_send
from nodnod.utils.aio import awaitable_noop
import types
import typing


class Value[T = typing.Any]:
    def __init__(self, cls: type[typing.Any], value: T, generator: Generator[T] | None = None):
        self.cls = cls
        self.value = value
        self.generator = generator

    def unbox(self) -> T:
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
        return f"<value of {getattr(self.cls, '__name__', self.cls)} = {self.value}{'' if self.generator is None else ' (open generator)'}>"


__all__ = ("Value",)
