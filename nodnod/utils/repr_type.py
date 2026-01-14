import typing


def type_repr(obj: typing.Any, /) -> str:
    return obj.__name__ if isinstance(obj, type) else str(obj)


__all__ = ("type_repr",)
