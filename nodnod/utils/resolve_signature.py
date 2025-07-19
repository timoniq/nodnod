import dataclasses
import typing
import inspect


@dataclasses.dataclass
class Signature:
    args: dict[str, type[typing.Any]]
    kwargs: dict[str, type[typing.Any]]

    def get_all_types(self) -> set[type[typing.Any]]:
        types = set[type[typing.Any]]()
        for t in self.args.values():
            types.add(t)
        for t in self.kwargs.values():
            types.add(t)
        return types


def resolve_signature(callable: typing.Callable[..., typing.Any], ignore_bound_parameters: bool = False) -> Signature:
    """Resolves callable signature"""

    if isinstance(callable, classmethod):
        callable = callable.__func__
    elif isinstance(callable, staticmethod):
        callable = callable.__func__

    sig = inspect.signature(callable)
    hints = typing.get_type_hints(callable)
    args: dict[str, type] = {}
    kwargs: dict[str, type] = {}

    for name, param in sig.parameters.items():
        if ignore_bound_parameters and name in {"cls", "self"}:
            continue

        typ = hints.get(name, typing.Any)
        if param.default is param.empty and param.kind in (
            param.POSITIONAL_ONLY, param.POSITIONAL_OR_KEYWORD
        ):
            args[name] = typ
        else:
            kwargs[name] = typ

    return Signature(args=args, kwargs=kwargs)
