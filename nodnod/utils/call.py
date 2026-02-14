from __future__ import annotations

import typing

from nodnod.utils.resolve_signature import resolve_signature


def call_with_context[R](function: typing.Callable[..., R], context: typing.Mapping[str, typing.Any]) -> R:
    signature = resolve_signature(function)
    args: list[typing.Any] = []
    kwargs: dict[str, typing.Any] = {}

    for t, args_params in {"args": signature.args, "kwargs": signature.kwargs}.items():
        for arg_param in args_params:
            if arg_param not in context and arg_param not in signature.optionals:
                raise NameNotFoundError(arg_param)

            if arg_param not in context:
                continue

            if t == "args":
                args.append(context[arg_param])

            if t == "kwargs":
                kwargs[arg_param] = context[arg_param]

    return function(*args, **kwargs)


class NameNotFoundError(Exception):
    def __init__(self, name: str, /) -> None:
        self.name = name

    def __str__(self) -> str:
        return f"Name `{self.name}` was not found."


__all__ = ("NameNotFoundError", "call_with_context")
