from __future__ import annotations

import typing

from nodnod.node import Node


def is_node(obj: typing.Any, /) -> typing.TypeIs[type[Node]]:
    return isinstance(obj, type) and issubclass(obj, Node)


__all__ = ("is_node",)
