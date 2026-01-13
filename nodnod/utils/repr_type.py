import sys

if sys.version_info >= (3, 14):  # pragma: no cover
    from annotationlib import type_repr

else:  # pragma: no cover
    import typing

    def type_repr(obj: typing.Any, /) -> str:
        return obj.__name__ if isinstance(obj, type) else str(obj)


__all__ = ("type_repr",)
