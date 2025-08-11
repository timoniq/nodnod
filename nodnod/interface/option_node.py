from __future__ import annotations

import typing
from functools import cache

from fntypes import Nothing, Option, Some

from nodnod.error import NodeBuildError
from nodnod.interface.is_node import is_node
from nodnod.utils.create_node import create_node

if typing.TYPE_CHECKING:
    from nodnod.node import Node

NOTHING_NODE: type[Node] | None = None
NOTHING: typing.Final = Nothing()


def get_nothing_node() -> type[Node]:
    from nodnod.node import Node

    global NOTHING_NODE

    if NOTHING_NODE is None:
        NOTHING_NODE = create_node(
            name="NothingNode",
            base_node=Node,
            bases=tuple(),
            namespace=dict(
                __dependencies__=set(),
                __compose__=lambda: NOTHING,
            ),
        )

    return NOTHING_NODE


@cache
def create_option_node(option: type[Option[typing.Any]], /) -> type[Node]:
    from nodnod.interface.either import SequentialEither
    from nodnod.node import Node

    args = typing.get_args(option)
    if not args:
        raise NodeBuildError("Option must have exactly one type argument.")

    arg_type = args[0]

    if is_node(typing.get_origin(arg_type) or arg_type):
        namespace = dict(__injected_types__=set(), __dependencies__={arg_type})
    else:
        namespace = dict(__injected_types__={arg_type}, __dependencies__=set())

    some_node = create_node(
        name="SomeNode",
        base_node=Node,
        bases=tuple(),
        namespace=dict(
            __bound_compose__=lambda values: Some(tuple(values)[0].value),
            __module__=__name__,
            **namespace,
        ),
    )
    return create_node(
        name="OptionNode",
        base_node=SequentialEither,
        bases=tuple(),
        namespace=dict(
            is_scalar=True,
            __type__=option,
            __either__=(some_node, get_nothing_node()),
            __module__=__name__,
        ),
    )


__all__ = ("create_option_node",)
