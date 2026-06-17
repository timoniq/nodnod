import typing

from nodnod.error import NodeBuildError

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
            count = max(len(args) - index - (len(parameters) - i - 1), 0)
            type_args[parameter] = tuple(args[index:index + count])
            index += count
        elif index < len(args):
            type_args[parameter] = args[index]
            index += 1
        elif parameter.has_default():
            type_args[parameter] = parameter.__default__
        else:
            # Too few type arguments and no PEP 696 default: fail loudly at parametrization
            # time instead of silently storing the `typing.NoDefault` sentinel as a value.
            raise NodeBuildError(
                f"Missing type argument for `{parameter.__name__}`: "
                f"expected at least {len(parameters)} type argument(s), got {len(args)}.",
            )

    return type_args


__all__ = ("get_type_args_values",)
