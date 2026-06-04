import typing

if typing.TYPE_CHECKING:
    from nodnod.value import Value


def prepare_values(values: dict[typing.Any, "Value[typing.Any]"]) -> dict[str, typing.Any]:
    """Unwraps scalar nodes into scalars and returns new dict"""
    prepared_values = {}

    for key, value in values.items():
        prepared_values[key] = value.unbox()

    return prepared_values


__all__ = ("prepare_values",)
