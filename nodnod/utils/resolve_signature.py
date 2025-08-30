import dataclasses
import inspect
import typing
from functools import cache

type AnnotationForm = typing.Any | typing.ForwardRef


@dataclasses.dataclass
class Signature:
    args: dict[str, type[typing.Any] | typing.ForwardRef]
    kwargs: dict[str, type[typing.Any] | typing.ForwardRef]
    var_positional: inspect.Parameter | None = None
    var_keyword: inspect.Parameter | None = None

    @property
    def var_positional_type(self) -> AnnotationForm | None:
        return self.var_positional.annotation if self.var_positional else None

    @property
    def var_keyword_type(self) -> AnnotationForm | None:
        return self.var_keyword.annotation if self.var_keyword else None

    def get_all_types(self) -> set[AnnotationForm]:
        types = set[type[typing.Any] | typing.ForwardRef]()
        for t in self.args.values():
            types.add(t)
        for t in self.kwargs.values():
            types.add(t)
        return types
    
    def merge(self) -> dict[str, typing.Any]:
        return self.args | self.kwargs


@cache
def resolve_signature(callable: typing.Callable[..., typing.Any], ignore_bound_parameters: bool = False) -> Signature:
    """Resolves callable signature"""

    if isinstance(callable, classmethod | staticmethod):
        callable = callable.__func__  # type: ignore

    sig = inspect.signature(callable)
    hints = callable.__annotations__
    args = {}
    kwargs = {}
    var_positional = None
    var_keyword = None

    for name, param in sig.parameters.items():
        if ignore_bound_parameters and name in {"cls", "self"}:
            continue

        if param.kind == inspect.Parameter.VAR_POSITIONAL:
            var_positional = param
            continue

        if param.kind == inspect.Parameter.VAR_KEYWORD:
            var_keyword = param
            continue

        typ = hints.get(name, typing.Any)

        if isinstance(typ, str):
            typ = typing.ForwardRef(typ)

        if param.default is param.empty and param.kind is param.POSITIONAL_ONLY:
            args[name] = typ
        else:
            kwargs[name] = typ

    return Signature(
        args=args, 
        kwargs=kwargs, 
        var_positional=var_positional, 
        var_keyword=var_keyword,
    )


__all__ = ("Signature", "resolve_signature")
