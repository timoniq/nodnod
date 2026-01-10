from __future__ import annotations

import typing

from nodnod.utils.create_node import create_node
from nodnod.utils.type_args import get_type_args_values

if typing.TYPE_CHECKING:
    from nodnod.interface.composable import Composable
    from nodnod.node import Node


def prepare_generic_node(
    composable: type[Composable[typing.Any]],
    type_args: typing.Any | tuple[typing.Any, ...],
) -> type[Node]:
    from nodnod.node import Node

    type_args = type_args if isinstance(type_args, tuple) else (type_args,)
    generic_nodes = getattr(composable, "__generics__", {})

    if type_args in generic_nodes:
        return generic_nodes[type_args]

    type_arg_dict = get_type_args_values(type_args, composable.__type_params__)
    generic_node = create_node(
        f"{composable.__name__}[{', '.join(type_arg.__name__ for type_arg in type_args)}]",
        base_node=Node,
        bases=(composable,),
        namespace=dict(
            __type_args__=type_arg_dict,
            __initialize__=None,
            __dependencies__=None,
            __module__=composable.__module__,
            __type_params__=composable.__type_params__,
        ),
    )
    generic_node.__type__ = generic_node
    generic_node.__init_subclass__()

    generic_nodes[type_args] = generic_node
    setattr(composable, "__generics__", generic_nodes)
    return generic_node


class generic_node:  # noqa: N801
    __node_cls__: type[Composable[typing.Any]]

    def __new__[T: Composable](cls, composable: type[T], /) -> type[T]:
        return type(
            composable.__name__ + ":" + "?",
            (cls,),
            dict(__node_cls__=composable, __module__=composable.__module__),
        )  # type: ignore

    def __class_getitem__(cls, type_args) -> typing.Any:
        return prepare_generic_node(cls.__node_cls__, type_args)


def create_type_arg_node(
    generic_node: type[Node],
    type_arg: typing.Any,
    node_type: typing.Any,
) -> type[Node]:
    from nodnod.node import Node

    return create_node(
        name=f"TypeArgNode[{type_arg.__name__}]",
        base_node=Node,
        bases=(),
        namespace=dict(
            __type__=node_type,
            __dependencies__=set(),
            __injections__=set(),
            __compose__=lambda: getattr(generic_node, "__type_args__", {})[type_arg],
            __module__=__name__,
        )
    )


__all__ = ("generic_node",)
