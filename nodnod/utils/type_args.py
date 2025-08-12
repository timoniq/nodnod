import typing

import fntypes

type AnnotationForm = typing.Any
type TypeParameter = typing.TypeVar | typing.TypeVarTuple | typing.ParamSpec
type TypeParameters = tuple[TypeParameter, ...]


def get_type_args(annotation: typing.Any, /) -> fntypes.Option[tuple[typing.Any, ...]]:
    type_args = typing.get_args(annotation)
    if not type_args:
        return fntypes.Nothing()
    return fntypes.Some(type_args)


def get_type_parameters(obj: typing.Any, /) -> dict[TypeParameter, AnnotationForm]:
    origin_obj = typing.get_origin(obj)
    args = get_type_args(obj).unwrap()
    parameters: TypeParameters = getattr(origin_obj or obj, "__parameters__")

    if not parameters:
        return {}

    index = 0
    generic_alias_args = dict[TypeParameter, typing.Any]()

    for parameter in parameters:
        if isinstance(parameter, typing.TypeVarTuple):
            stop_index = len(args) - index
            generic_alias_args[parameter] = args[index:stop_index]
            index = stop_index
            continue

        arg = args[index] if index < len(args) else None
        generic_alias_args[parameter] = arg
        index += 1

    return generic_alias_args


__all__ = ("get_type_args", "get_type_parameters")
