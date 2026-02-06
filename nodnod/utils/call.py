from __future__ import annotations

import typing

from nodnod.utils.resolve_signature import resolve_signature


def call_with_context[R](function: typing.Callable[..., R], context: dict[str, typing.Any]) -> R:
    signature = resolve_signature(function)
    args: list[typing.Any] = []
    kwargs: dict[str, typing.Any] = {}

    for t, args_params in {"args": signature.args, "kwargs": signature.kwargs}.items():
        for arg_param in args_params:
            if arg_param not in context and arg_param not in signature.optionals:
                raise KeyError(arg_param)

            if arg_param not in context:
                continue

            if t == "args":
                args.append(context[arg_param])

            if t == "kwargs":
                kwargs[arg_param] = context[arg_param]

    return function(*args, **kwargs)


__all__ = ("call_with_context",)
