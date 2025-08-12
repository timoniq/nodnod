import typing

import fntypes

type AnnotationForm = typing.Any
type TypeParameter = typing.TypeVar | typing.TypeVarTuple | typing.ParamSpec
type TypeParameters = tuple[TypeParameter, ...]


def get_type_args(obj: typing.Any, /) -> dict[TypeParameter, AnnotationForm]:
    origin_obj = typing.get_origin(obj)
    args = typing.get_args(obj)
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


def get_type_parameters(obj: typing.Any) -> TypeParameters:
    return getattr(obj, "__parameters__", ())


__all__ = ("get_type_args", "get_type_parameters")
