from __future__ import annotations

import typing

from kungfu import Error, Ok, Result

from nodnod.utils.resolve_signature import resolve_signature


def call_with_context[R](
    function: typing.Callable[..., R],
    context: typing.Mapping[str, typing.Any],
) -> Result[R, str]:
    signature = resolve_signature(function)
    args: list[typing.Any] = []
    kwargs: dict[str, typing.Any] = {}

    for t, args_params in {"args": signature.args, "kwargs": signature.kwargs}.items():
        for arg_param in args_params:
            if arg_param not in context and arg_param not in signature.optionals:
                return Error(arg_param)

            if arg_param not in context:
                continue

            if t == "args":
                args.append(context[arg_param])

            if t == "kwargs":
                kwargs[arg_param] = context[arg_param]

    return Ok(function(*args, **kwargs))


__all__ = ("call_with_context",)
