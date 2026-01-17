import typing
from contextlib import suppress

from typing_extensions import Format, ForwardRef, evaluate_forward_ref


def get_injection_type(
    injection: typing.Any,
    /,
    *,
    owner: typing.Any | None = None,
) -> typing.Any:
    args = typing.get_args(injection)

    if not args:
        raise ValueError("Injection must have one type argument.")

    arg = args[0]

    if isinstance(arg, str):
        arg = ForwardRef(arg, is_class=isinstance(owner, type) if owner is not None else False)

    if isinstance(arg, ForwardRef):
        with suppress(NameError):
            arg = evaluate_forward_ref(arg, owner=owner, format=Format.VALUE)

    return arg


__all__ = ("get_injection_type",)
