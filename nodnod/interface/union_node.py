from __future__ import annotations

import types
import typing
from functools import cache

from nodnod.error import NodeBuildError
from nodnod.interface.create_result_node import create_result_node, is_result
from nodnod.interface.is_node import first_arg_is_composable
from nodnod.interface.option_node import create_option_node, is_option
from nodnod.utils.create_node import create_node, create_node_from_composable
from nodnod.utils.repr_type import type_repr

if typing.TYPE_CHECKING:
    from nodnod.node import Node

NONE_TYPES: typing.Final = frozenset({None, type(None)})
UNION_TYPES: typing.Final = frozenset((typing.Union, types.UnionType))


def is_union(obj: typing.Any, /) -> typing.TypeIs[types.UnionType]:
    return (typing.get_origin(obj) or obj) in UNION_TYPES and first_arg_is_composable(obj)


@cache
def get_none_node() -> type[Node]:
    from nodnod.node import Node

    node = create_node(
        name="NoneNode",
        base_node=Node,
        bases=tuple(),
        namespace=dict(
            __dependencies__=set(),
            __injections__=set(),
            __initialize__=lambda _: None,
            __module__=__name__,
        ),
    )
    setattr(node, "__traverse__", [node])
    setattr(node, "__type__", node)
    return node


@cache
def create_union_node(union: types.UnionType, /) -> type[Node]:
    from nodnod.interface.either import SequentialEither
    from nodnod.interface.is_node import is_node

    args = typing.get_args(union)
    if not args:
        raise NodeBuildError("Union must have at least one type argument.")

    is_optional = False
    either: list[type[Node]] = list()
    injected_types: set[typing.Any] = set()

    for arg in args:
        if arg in NONE_TYPES:
            is_optional = True
            continue

        origin_arg = typing.get_origin(arg) or arg

        if is_node(origin_arg):
            either.append(origin_arg)
        elif hasattr(origin_arg, "__compose__"):
            either.append(create_node_from_composable(arg))
        elif is_option(arg):
            either.append(create_option_node(arg))
        elif is_result(arg):
            either.append(create_result_node(arg))
        else:
            injected_types.add(arg)

    if is_optional:
        either.append(get_none_node())

    union_node = create_node(
        name="UnionNode[{}]".format(", ".join(type_repr(arg) for arg in args)),
        base_node=SequentialEither,
        bases=tuple(),
        namespace=dict(
            is_scalar=True,
            __type__=union,
            __either__=tuple(either),
            __module__=__name__,
        ),
    )
    union_node.__injections__ = injected_types
    return union_node


__all__ = ("create_union_node", "is_union")
