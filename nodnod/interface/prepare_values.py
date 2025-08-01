import typing

from nodnod.node import Node


def prepare_values(values: dict[typing.Any, Node[typing.Any]]) -> dict[str, typing.Any]:
    prepared_values = {}

    for key, node in values.items():
        if node.is_scalar:
            prepared_values[key] = node.value
        else:
            prepared_values[key] = node

    return prepared_values


__all__ = ("prepare_values",)
