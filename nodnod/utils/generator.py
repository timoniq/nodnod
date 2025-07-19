import typing
import contextlib
import fntypes



async def generator_asend[T, Send](generator: typing.AsyncGenerator[T, Send], send: Send = None) -> fntypes.Option[T]:
    with contextlib.suppress(StopAsyncIteration):
        value = await generator.asend(send)
        return fntypes.Some(value)
    return fntypes.Nothing()


def generator_send[T, Send](generator: typing.Generator[T, Send, None], send: Send = None) -> fntypes.Option[T]:
    with contextlib.suppress(StopIteration):
        value = generator.send(send)
        return fntypes.Some(value)
    return fntypes.Nothing()
