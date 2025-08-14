import typing

type AnnotationForm = typing.Any
type TypeParameter = typing.TypeVar | typing.TypeVarTuple | typing.ParamSpec
type TypeParameters = tuple[TypeParameter, ...]


def get_type_args_values(args: tuple[typing.Any, ...], parameters: TypeParameters) -> dict[typing.TypeVar, typing.Any]:
    if not parameters:
        return {}

    type_args = {}   
    index = 0

    for i, parameter in enumerate(parameters):
        if isinstance(parameter, typing.TypeVarTuple):
            index += max(len(args) - index - (len(parameters) - i - 1), 0)
        elif index < len(args):
            type_args[parameter] = args[index]
            index += 1
        else:
            type_args[parameter] = parameter.__default__ 

    return type_args


__all__ = ("get_type_args_values",)
