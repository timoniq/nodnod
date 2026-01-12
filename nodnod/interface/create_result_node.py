import typing
from functools import cache

import kungfu

from nodnod.error import NodeBuildError
from nodnod.utils.create_node import create_node

if typing.TYPE_CHECKING:
   from nodnod.interface.result_node import ResultNode


@cache
def create_result_node[T, Err: Exception](result: type[kungfu.Result[T, Err]]) -> type["ResultNode[T, Err]"]:
   from nodnod.interface.result_node import ResultNode

   args = typing.get_args(result)
   if not args:
      raise NodeBuildError("Result must have specified type arguments")

   node_cls = args[0]
   error_cls = args[1]

   return create_node(
      name=f"ResultNode[{node_cls.__name__}, {error_cls.__name__}]",
      base_node=ResultNode,
      bases=(),
      namespace=dict(
         __type__=result,
         __from_node__=node_cls,
         __error__=error_cls,
         __module__=__name__,
      ),
   )


__all__ = ("create_result_node",)
