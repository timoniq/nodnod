from nodnod.node import Node
import fntypes


class ResultNode[T, Err: Exception](Node[fntypes.Result[T, Err]]):
   __from_node__: type[Node]
   __error__: type[Err] | tuple[type[Err], ...]

   def __init_subclass__(cls, abstract: bool = False) -> None:
      if not abstract:
         cls.__dependencies__ = {cls.__from_node__}
         cls.__injections__ = set()
         cls.__type__ = cls.__type__ or cls

   @classmethod
   def __compose__(cls, err: BaseException) -> fntypes.Pulse[BaseException]:
      try:
         raise err
      except cls.__error__:
         return fntypes.Ok()
      except BaseException as e:
         return fntypes.Error(e)
