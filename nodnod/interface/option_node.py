from __future__ import annotations

import typing
from functools import cache

from kungfu import Nothing, Option, Some

from nodnod.error import NodeBuildError
from nodnod.interface.is_node import first_arg_is_node, is_node
from nodnod.utils.create_node import create_node
from nodnod.utils.is_type import is_type
from nodnod.utils.repr_type import type_repr

if typing.TYPE_CHECKING:
    from nodnod.node import Node

NOTHING: typing.Final = Nothing()


def is_option(dep_type: typing.Any, /) -> typing.TypeIs[type[Option[typing.Any]]]:
    return is_type(dep_type, Option) and first_arg_is_node(dep_type)


@cache
def get_nothing_node() -> type[Node]:
    from nodnod.node import Node

    node = create_node(
        name="NothingNode",
        base_node=Node,
        bases=tuple(),
        namespace=dict(
            __dependencies__=set(),
            __injections__=set(),
            __initialize__=lambda _: NOTHING,
            __module__=__name__,
        ),
    )
    setattr(node, "__traverse__", [node])
    setattr(node, "__type__", node)
    return node


@cache
def create_option_node(option: type[Option[typing.Any]], /) -> type[Node]:
    from nodnod.interface.either import SequentialEither
    from nodnod.node import Node

    args = typing.get_args(option)
    if not args:
        raise NodeBuildError("Option must have exactly one type argument.")

    arg_type = args[0]

    if is_node(typing.get_origin(arg_type) or arg_type):
        namespace = dict(__injections__=set(), __dependencies__={arg_type})
    else:
        namespace = dict(__injections__={arg_type}, __dependencies__=set())

    some_node = create_node(
        name=f"SomeNode[{type_repr(arg_type)}]",
        base_node=Node,
        bases=tuple(),
        namespace=dict(
            __initialize__=lambda values: Some(tuple(values)[0].value),
            __module__=__name__,
            **namespace,
        ),
    )
    return create_node(
        name=f"OptionNode[{type_repr(arg_type)}]",
        base_node=SequentialEither,
        bases=tuple(),
        namespace=dict(
            is_scalar=True,
            __type__=option,
            __either__=(some_node, get_nothing_node()),
            __module__=__name__,
        ),
    )


__all__ = ("create_option_node", "is_option")
