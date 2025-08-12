import typing


class Composable[T](typing.Protocol):
    @classmethod
    def __compose__(cls, *args: typing.Any, **kwargs: typing.Any) -> T:
        ...


__all__ = ("Composable",)
