import contextlib
import typing

import kungfu


async def generator_asend[T, Send](
    generator: typing.AsyncGenerator[T, Send], send: Send = None
) -> kungfu.Option[T]:
    with contextlib.suppress(StopAsyncIteration):
        value = await generator.asend(send)
        return kungfu.Some(value)
    return kungfu.Nothing()


def generator_send[T, Send](generator: typing.Generator[T, Send, None], send: Send = None) -> kungfu.Option[T]:
    with contextlib.suppress(StopIteration):
        value = generator.send(send)
        return kungfu.Some(value)
    return kungfu.Nothing()


__all__ = ("generator_asend", "generator_send")
