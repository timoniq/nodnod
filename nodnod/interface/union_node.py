from __future__ import annotations

import types
import typing
from functools import cache

import fntypes

from nodnod.error import NodeBuildError
from nodnod.interface.option_node import create_option_node
from nodnod.utils.create_node import create_node

if typing.TYPE_CHECKING:
    from nodnod.node import Node

NONE_NODE: type[Node] | None = None
NONE_TYPES: typing.Final = frozenset({None, type(None)})
UNION_TYPES: typing.Final = frozenset((typing.Union, types.UnionType))


def is_union(obj: typing.Any, /) -> typing.TypeIs[types.UnionType]:
    return obj in UNION_TYPES


def get_none_node() -> type[Node]:
    from nodnod.node import Node
    
    global NONE_NODE
    
    if NONE_NODE is None:
        NONE_NODE = create_node(
            name="NoneNode",
            base_node=Node,
            bases=tuple(),
            namespace=dict(__dependencies__=set()),
        )

    return NONE_NODE


@cache
def create_union_node(union: types.UnionType, /) -> type[Node]:
    from nodnod.interface.either import SequentialEither
    from nodnod.interface.is_node import is_node

    args = typing.get_args(union)
    if not args:
        raise NodeBuildError("Union must have at least one type argument.")

    is_optional = False
    either = list()
    injected_types = set()

    for arg in args:
        if arg in UNION_TYPES:
            is_optional = True
            continue
        
        origin_arg = typing.get_origin(arg) or arg

        if is_node(origin_arg):
            either.append(arg)
        elif origin_arg is fntypes.Option:
            either.append(create_option_node(arg)) 
        else:
            injected_types.add(arg)

    return create_node(
        name="UnionNode",
        base_node=SequentialEither,
        bases=tuple(),
        namespace=dict(
            is_scalar=True,
            __injected_types__=injected_types,  # FIXME: need refactoring
            __type__=union,
            __either__=tuple(either) + ((get_none_node(),) if is_optional else ()),
            __module__=__name__,
        ),
    )


__all__ = ("create_union_node",)
