from __future__ import annotations

import typing

from nodnod.interface.composable import Composable
from nodnod.node import Node


def is_node(obj: typing.Any, /) -> typing.TypeIs[type[Node]]:
    return isinstance(obj, type) and issubclass(obj, Node)


def first_arg_is_composable(generic_alias: typing.Any, /) -> typing.TypeIs[type[Composable]]:
    args = typing.get_args(generic_alias)

    if not args:
        return False

    first_arg = args[0]
    return hasattr(typing.get_origin(first_arg) or first_arg, "__compose__")


__all__ = ("is_node", "first_arg_is_composable")
