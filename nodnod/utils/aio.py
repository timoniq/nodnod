import inspect
import typing


async def maybe_awaitable[T](value: T | typing.Awaitable[T], /) -> T:
    if inspect.isawaitable(value):
        return await value
    return value


class awaitable_noop:  # noqa: N801
    def __await__(self) -> typing.Generator[None, None, typing.Any]:
        return iter(())  # type: ignore


__all__ = ("awaitable_noop", "maybe_awaitable")
