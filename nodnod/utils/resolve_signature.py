import dataclasses
import inspect
import sys
import typing
from functools import cache

from typing_extensions import Format, evaluate_forward_ref, get_annotations

type AnnotationForm = typing.Any | typing.ForwardRef


@dataclasses.dataclass
class Signature:
    args: dict[str, AnnotationForm]
    kwargs: dict[str, AnnotationForm]
    var_positional: inspect.Parameter | None = None
    var_keyword: inspect.Parameter | None = None

    @property
    def var_positional_type(self) -> AnnotationForm | None:
        return self.var_positional.annotation if self.var_positional else None

    @property
    def var_keyword_type(self) -> AnnotationForm | None:
        return self.var_keyword.annotation if self.var_keyword else None

    def get_all_types(self) -> set[AnnotationForm]:
        types: set[AnnotationForm] = set()

        for t in self.args.values():
            types.add(t)

        for t in self.kwargs.values():
            types.add(t)

        return types

    def merge(self) -> dict[str, AnnotationForm]:
        return self.args | self.kwargs


@cache
def resolve_callable_annotations(obj: typing.Callable[..., typing.Any], /) -> dict[str, AnnotationForm]:
    """Resolves callable annotations"""

    annotations: dict[str, AnnotationForm] = {}

    for name, annotation in get_annotations(obj, eval_str=False, format=Format.FORWARDREF).items():
        if isinstance(annotation, str):
            module = sys.modules.get(obj_mod, None) if (obj_mod := getattr(obj, "__module__", None)) is not None else None
            annotation = typing.ForwardRef(arg=annotation, is_argument=True, module=module)

        if not isinstance(annotation, typing.ForwardRef):
            annotations[name] = annotation
            continue

        try:
            value = evaluate_forward_ref(annotation, owner=obj, format=Format.VALUE)
        except NameError:
            annotations[name] = annotation
        else:
            annotations[name] = value

    return annotations


@cache
def resolve_signature(callable: typing.Callable[..., typing.Any], ignore_bound_parameters: bool = False) -> Signature:
    """Resolves callable signature"""

    if isinstance(callable, classmethod | staticmethod):
        callable = callable.__func__  # type: ignore

    sig = inspect.signature(callable)
    hints = resolve_callable_annotations(callable)
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
