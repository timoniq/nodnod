import types
import typing
from reprlib import recursive_repr

from nodnod.node import Generator
from nodnod.utils.aio import awaitable_noop
from nodnod.utils.generator import generator_asend, generator_send
from nodnod.utils.repr_type import type_repr

type AnyType = typing.Any


class Value[T = typing.Any]:
    def __init__(self, cls: AnyType, value: T, generator: Generator[T] | None = None) -> None:
        self.cls = cls
        self.value = value
        self.generator = generator

    def unbox(self) -> T:
        return self.value

    def close(self) -> typing.Awaitable[typing.Any]:
        generator = self.generator
        if generator is None:
            return awaitable_noop()

        self.generator = None

        if isinstance(generator, types.AsyncGeneratorType):
            return self._aclose(generator)

        # Sync generator: resume once to run the post-yield teardown (the `yield value; cleanup`
        # idiom), then force-close if it yielded again, so a multi-yield generator is not left
        # suspended (its finally/cleanup leaked to non-deterministic GC).
        if isinstance(generator, types.GeneratorType) and generator_send(generator):
            generator.close()

        return awaitable_noop()

    async def _aclose(self, generator: "typing.AsyncGenerator[T, None]") -> None:
        if await generator_asend(generator):
            await generator.aclose()

    @recursive_repr()
    def __repr__(self) -> str:
        return f"<value of {type_repr(self.cls)} = {self.value}{'' if self.generator is None else ' (open generator)'}>"


__all__ = ("Value",)
