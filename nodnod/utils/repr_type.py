import typing


def type_repr(obj: typing.Any, /) -> str:
    return obj.__name__ if isinstance(obj, type) else repr(obj)


__all__ = ("type_repr",)
