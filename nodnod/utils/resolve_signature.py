import dataclasses
import inspect
import sys
import types
import typing
from functools import cache

from typing_extensions import Format, ForwardRef, evaluate_forward_ref, get_annotations

type AnnotationForm = ForwardRef | typing.Any


def is_routine_method(obj: typing.Any, /) -> bool:
    return inspect.isbuiltin(obj) or inspect.ismethod(obj) or inspect.ismethodwrapper(obj)


def is_routine_descriptor(obj: typing.Any, /) -> bool:
    return (
        inspect.ismethoddescriptor(obj)
        or inspect.isgetsetdescriptor(obj)
        or isinstance(obj, types.ClassMethodDescriptorType)
    )


@dataclasses.dataclass
class Signature:
    args: dict[str, AnnotationForm]
    kwargs: dict[str, AnnotationForm]
    optionals: set[str] = dataclasses.field(default_factory=set)
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
def resolve_callable_annotations(
    obj: typing.Callable[..., typing.Any],
    /,
    *,
    bound_class: type[typing.Any] | None = None,
) -> dict[str, AnnotationForm]:
    """Resolves callable annotations"""

    annotations: dict[str, AnnotationForm] = {}
    localns: dict[str, typing.Any] | None = None

    if bound_class is not None:
        localns = {param.__name__: param for param in getattr(bound_class, "__type_params__", ())}
        localns |= {
            k: v
            for k, v in bound_class.__dict__.items()
            if not is_routine_method(v) and not is_routine_descriptor(v)
        }

    for name, annotation in get_annotations(
        obj,
        locals=localns,
        eval_str=False,
        format=Format.FORWARDREF,
    ).items():
        if isinstance(annotation, str):
            module = (
                sys.modules.get(obj_mod, None)
                if (obj_mod := getattr(obj, "__module__", None)) is not None
                else None
            )
            annotation = ForwardRef(arg=annotation, is_argument=True, module=module)

        if not isinstance(annotation, ForwardRef):
            annotations[name] = annotation
            continue

        try:
            value = evaluate_forward_ref(
                forward_ref=annotation,
                owner=obj,
                locals=localns,
                format=Format.VALUE,
            )
        except NameError:
            annotations[name] = annotation
        else:
            annotations[name] = value

    return annotations


@cache
def resolve_signature(
    callable: typing.Callable[..., typing.Any],
    bound_class: type[typing.Any] | None = None,
    ignore_bound_parameters: bool = False,
) -> Signature:
    """Resolves callable signature"""

    if isinstance(callable, classmethod | staticmethod):
        callable = callable.__func__  # type: ignore

    if sys.version_info >= (3, 14):  # pragma: no cover
        sig = inspect.signature(callable, annotation_format=Format.STRING)
    else:  # pragma: no cover
        sig = inspect.signature(callable)

    hints = resolve_callable_annotations(callable, bound_class=bound_class)
    args = {}
    kwargs = {}
    optionals = set()
    var_positional = None
    var_keyword = None

    for name, param in sig.parameters.items():
        if ignore_bound_parameters and name in {"cls", "self"}:
            continue

        if param.default is not param.empty:
            optionals.add(name)

        if param.kind in (inspect.Parameter.VAR_POSITIONAL, inspect.Parameter.VAR_KEYWORD):
            param._annotation = hints.get(name, getattr(param, "_annotation", typing.Any))
            var_positional = param if param.kind == inspect.Parameter.VAR_POSITIONAL else var_positional
            var_keyword = param if param.kind == inspect.Parameter.VAR_KEYWORD else var_keyword
            continue

        typ = hints.get(name, typing.Any)
        if param.default is param.empty and param.kind is param.POSITIONAL_ONLY:
            args[name] = typ
        else:
            kwargs[name] = typ

    return Signature(
        args=args,
        kwargs=kwargs,
        optionals=optionals,
        var_positional=var_positional,
        var_keyword=var_keyword,
    )


__all__ = ("Signature", "resolve_signature", "resolve_callable_annotations")
