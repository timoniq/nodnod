import typing


@typing.runtime_checkable
class Composable[T = typing.Any](typing.Protocol):
    @classmethod
    def __compose__(cls, *args: typing.Any, **kwargs: typing.Any) -> T: ...


__all__ = ("Composable",)
