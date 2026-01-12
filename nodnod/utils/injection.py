import typing

from typing_extensions import Format, ForwardRef, evaluate_forward_ref

if typing.TYPE_CHECKING:
    from nodnod.node import Injection


def get_injection_type(
    injection: type[Injection[typing.Any]],
    /,
    *,
    owner: typing.Any | None = None,
) -> typing.Any:
    args = typing.get_args(injection)

    if len(args) != 1:
        raise ValueError("Injection must have at least one type argument.")

    arg = args[0]

    if isinstance(arg, str):
        arg = ForwardRef(arg, is_argument=True, is_class=isinstance(owner, type) if owner is not None else False)

    if isinstance(arg, ForwardRef):
        try:
            arg = evaluate_forward_ref(arg, owner=owner, format=Format.VALUE)
        except NameError:
            return arg

    return arg


__all__ = ("get_injection_type",)
