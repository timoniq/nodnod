import kungfu

from nodnod.node import Node


class ResultNode[T, Err: BaseException](Node[kungfu.Result[T, Err]]):
	__from_node__: type[Node]
	__error__: type[Err] | tuple[type[Err], ...]

	def __init_subclass__(cls, abstract: bool = False) -> None:
		if not abstract:
			cls.__dependencies__ = {cls.__from_node__}  # type: ignore
			cls.__injections__ = set()  # type: ignore
			cls.__type__ = cls.__type__ or cls

	@classmethod
	def __compose__(cls, err: BaseException) -> kungfu.Pulse[BaseException]:
		try:
			raise err
		except cls.__error__:
			return kungfu.Ok()
		except BaseException as e:
			return kungfu.Error(e)


__all__ = ("ResultNode",)
