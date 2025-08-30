from __future__ import annotations

import typing

if typing.TYPE_CHECKING:
    from nodnod.utils.resolve_signature import Signature


def bundle[R](
    function: typing.Callable[..., R],
    signature: Signature,
    context: dict[str, typing.Any],
) -> R:
    args = tuple(context[arg_param] for arg_param in signature.args)
    kwargs = {kw_param: context[kw_param] for kw_param in signature.kwargs}
    return function(*args, **kwargs)


__all__ = ("bundle",)
