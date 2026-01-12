from __future__ import annotations

import types
import typing
from functools import cache

import kungfu

from nodnod.error import NodeBuildError
from nodnod.interface.node_from_function import Externals, initialize_node_with_externals
from nodnod.interface.option_node import create_option_node
from nodnod.node import Injection
from nodnod.utils.create_node import create_node
from nodnod.utils.injection import get_injection_type
from nodnod.utils.is_type import is_type

if typing.TYPE_CHECKING:
    from nodnod.node import Node

NONE_TYPES: typing.Final = frozenset({None, type(None)})
UNION_TYPES: typing.Final = frozenset((typing.Union, types.UnionType))


def is_union(obj: typing.Any, /) -> typing.TypeIs[types.UnionType]:
    return typing.get_origin(obj) in UNION_TYPES


@cache
def get_none_node() -> type[Node]:
    from nodnod.node import Node
    return create_node(
        name="NoneNode",
        base_node=Node,
        bases=tuple(),
        namespace=dict(__dependencies__=set()),
    )


@cache
def create_union_node(
    union: types.UnionType,
    /,
    *,
    owner: typing.Any | None = None,
    is_from_function: bool = False,
) -> type[Node]:
    from nodnod.interface.either import SequentialEither
    from nodnod.interface.is_node import is_node

    args = typing.get_args(union)
    if not args:
        raise NodeBuildError("Union must have at least one type argument.")

    is_optional = False
    either = list()
    injected_types = set()

    for arg in args:
        if arg in NONE_TYPES:
            is_optional = True
            continue

        origin_arg = typing.get_origin(arg) or arg

        if is_node(origin_arg):
            either.append(arg)
        elif origin_arg is kungfu.Option:
            either.append(create_option_node(arg))
        elif is_from_function and is_type(arg, Injection):
            injected_types.add(get_injection_type(arg, owner=owner))
        elif not is_from_function:
            injected_types.add(arg)

    node = create_node(
        name="UnionNode[{}]".format(", ".join(str(arg) for arg in args)),
        base_node=SequentialEither,
        bases=tuple(),
        namespace=dict(
            is_scalar=True,
            __injections__=injected_types,
            __type__=union,
            __either__=tuple(either) + ((get_none_node(),) if is_optional else ()),
            __module__=__name__,
        ),
    )

    if is_from_function:
        node.__injections__.add(Externals)
        setattr(node, "__initialize__", initialize_node_with_externals)

    return node


__all__ = ("create_union_node",)
