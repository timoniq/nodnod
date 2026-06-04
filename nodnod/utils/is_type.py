import typing


@typing.overload
def is_type[T](annotation: typing.Any, t: type[T], /) -> typing.TypeIs[type[T]]: ...


@typing.overload
def is_type[T](annotation: typing.Any, t: typing.Any, /) -> bool: ...


def is_type[T](annotation: typing.Any, t: typing.Any | tuple[typing.Any, ...], /) -> bool:
    if isinstance(t, tuple):
        return any(is_type(annotation, t_type) for t_type in t)

    orig_annotation = typing.get_origin(annotation) or annotation
    origin_type = typing.get_origin(t) or t

    ann_type_args = typing.get_args(annotation)
    t_type_args = typing.get_args(t)

    if (
        orig_annotation is not origin_type
        and not (
            isinstance(orig_annotation, type)
            and isinstance(origin_type, type)
            and issubclass(orig_annotation, origin_type)
        )
    ):
        return False

    if not t_type_args:
        return True

    return ann_type_args == t_type_args


__all__ = ("is_type",)
