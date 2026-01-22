from __future__ import annotations

import typing

from nodnod.utils.resolve_signature import resolve_signature


def call_with_context[R](function: typing.Callable[..., R], context: dict[str, typing.Any]) -> R:
    signature = resolve_signature(function)
    args = tuple(
        context[arg_param]
        for arg_param in signature.args
        if arg_param in context or arg_param not in signature.optionals
    )
    kwargs = {
        kw_param: context[kw_param]
        for kw_param in signature.kwargs
        if kw_param in context or kw_param not in signature.optionals
    }
    return function(*args, **kwargs)


__all__ = ("call_with_context",)
