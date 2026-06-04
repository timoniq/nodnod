import typing
from functools import cache

import kungfu

from nodnod.error import NodeBuildError
from nodnod.interface.is_node import first_arg_is_composable, is_node
from nodnod.utils.create_node import create_node, create_node_from_composable
from nodnod.utils.is_type import is_type
from nodnod.utils.repr_type import type_repr

if typing.TYPE_CHECKING:
    from nodnod.interface.result_node import ResultNode


def is_result(dep_type: typing.Any, /) -> typing.TypeIs[type[kungfu.Result[typing.Any, typing.Any]]]:
    return is_type(dep_type, kungfu.Result) and first_arg_is_composable(dep_type)


@cache
def create_result_node[T, Err: Exception](result: type[kungfu.Result[T, Err]]) -> type["ResultNode[T, Err]"]:
    from nodnod.interface.result_node import ResultNode

    args = typing.get_args(result)
    if not args:
        raise NodeBuildError("Result must have specified type arguments.")

    node_cls = args[0]
    error_cls = args[1]

    return create_node(
        name=f"ResultNode[{type_repr(node_cls)}, {type_repr(error_cls)}]",
        base_node=ResultNode,
        bases=(),
        namespace=dict(
            __type__=result,
            __from_node__=create_node_from_composable(node_cls) if not is_node(node_cls) else node_cls,
            __error__=error_cls,
            __module__=__name__,
        ),
    )


__all__ = ("create_result_node", "is_result")
