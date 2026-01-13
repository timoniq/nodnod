from __future__ import annotations

import types
import typing

from nodnod.node import Node


def is_node(obj: typing.Any, /) -> typing.TypeIs[type[Node]]:
    return isinstance(obj, type) and issubclass(obj, Node)


def first_arg_is_node(generic_alias: types.GenericAlias, /) -> bool:
    args = typing.get_args(generic_alias)

    if not args:
        return False

    first_arg = args[0]
    return is_node(typing.get_origin(first_arg) or first_arg)


__all__ = ("is_node", "first_arg_is_node")
