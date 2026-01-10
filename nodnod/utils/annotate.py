import typing
from functools import partial

from typing_extensions import ForwardRef

type DependencyName = str
type DependsAnnotate = typing.Callable[
    [typing.Callable[..., typing.Any], dict[str, ForwardRef]],
    dict[str, typing.Any],
]


def is_depends_annotatable[**P, R](obj: typing.Callable[P, R], /) -> typing.TypeIs["DependsAnnotatable[P, R]"]:
    return isinstance(obj, DependsAnnotatable)


@typing.runtime_checkable
class DependsAnnotatable[**P, R](typing.Protocol):
    def __call__(self, *args: P.args, **kwargs: P.kwargs) -> R:
        ...

    def __nodnod_depends_annotate__(
        self,
        depends_forward_refs: dict[DependencyName, ForwardRef],
        /,
    ) -> dict[str, typing.Any]:
        ...


class depends_annotate:  # noqa: N801
    @classmethod
    def via(cls, annotate: DependsAnnotate, /) -> typing.Self:
        return cls(annotate)

    def __init__(self, annotate: DependsAnnotate, /) -> None:
        self.annotate = annotate

    def __call__[T: typing.Callable[..., typing.Any]](self, func: T, /) -> T:
        func.__nodnod_depends_annotate__ = partial(self.annotate, func)
        return func


__all__ = ("depends_annotate",)
