import typing

if typing.TYPE_CHECKING:
    from nodnod.node import Node


def prepare_value(node: "Node[typing.Any]") -> typing.Any:
    if node.is_scalar:
        return node.value
    return node


def prepare_values(values: dict[typing.Any, "Node[typing.Any]"]) -> dict[str, typing.Any]:
    """Unwraps scalar nodes into scalars and returns new dict"""
    prepared_values = {}

    for key, node in values.items():
        prepared_values[key] = prepare_value(node)

    return prepared_values


__all__ = ("prepare_values", "prepare_value")
