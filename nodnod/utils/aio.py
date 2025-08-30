import typing


class awaitable_noop:
    def __await__(self) -> typing.Generator[None, None, typing.Any]:
        return iter(())  # type: ignore


__all__ = ("awaitable_noop",)
