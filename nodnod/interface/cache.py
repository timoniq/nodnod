from __future__ import annotations

import inspect
import typing
from datetime import datetime, timedelta

from nodnod.utils.aio import maybe_awaitable
from nodnod.utils.create_node import create_node, create_node_from_composable


if typing.TYPE_CHECKING:
    from nodnod.node import Node
    from nodnod.interface.composable import Composable


class cache(timedelta):
    def __call__[T](self, composable: type[T], /) -> type[T]:
        if not hasattr(composable, "__compose__"):
            raise RuntimeError("cache decorator can only be used with a composable class")

        if self.total_seconds() <= 0:
            raise RuntimeError("cache time must be greater than 0")

        return create_node(  # type: ignore
            name=f"CachedNode:{composable.__name__}",
            base_node=create_node_from_composable(composable),  # type: ignore
            bases=(),
            namespace=dict(
                __type__=composable,
                __compose__=classmethod(self.__compose__),
                __compose_inner__=getattr(composable, "__compose__"),
                __cache_time__=self,
                __last_cache_time__=None,
                __module__=composable.__module__,
                __initialize__=None,
            ),
        )

    @staticmethod
    async def __compose__(cls: type[Node], *args: typing.Any, **kwargs: typing.Any) -> typing.Any:
        if (
            not hasattr(cls, "__cache__")
            or (
                getattr(cls, "__last_cache_time__") is not None
                and datetime.now() - getattr(cls, "__last_cache_time__") >= getattr(cls, "__cache_time__")
            )
        ):
            compose_inner = getattr(cls, "__compose_inner__")

            if inspect.isasyncgenfunction(compose_inner):
                gen = compose_inner(*args, **kwargs)
                response = await gen.__anext__()
            elif inspect.isgeneratorfunction(compose_inner):
                gen = compose_inner(*args, **kwargs)
                response = next(gen)
            else:
                response = await maybe_awaitable(compose_inner(*args, **kwargs))

            setattr(cls, "__cache__", response)
            setattr(cls, "__last_cache_time__", datetime.now())
            return response

        return getattr(cls, "__cache__")


__all__ = ("cache",)
