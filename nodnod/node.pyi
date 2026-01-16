import typing
from typing import Annotated as Annotate

import kungfu

from nodnod.value import Value

type Injection[T] = T
type ComposeResponse[T = typing.Any] = T | Node[T] | typing.Awaitable[T] | typing.Generator[T, None, None] | typing.AsyncGenerator[T, None]
type InjectionHook = typing.Callable[[type[Node], str, typing.Any], kungfu.Pulse[str]]
type Queue = list[type[Node]]

def dummy_compose(cls: type[typing.Any]) -> typing.NoReturn: ...
def initialize_forward_refs(forward_refs: dict[str, typing.Any], *, is_from_function: bool = False) -> None: ...

class Node[T = typing.Any, Root = typing.Any]:
    __type__: typing.Any
    __dependencies__: set[type[Node]]
    __injections__: set[typing.Any]
    __traverse__: Queue
    __initialize__: typing.Callable[[set[Value]], ComposeResponse[T]]
    __compose__: typing.Callable[..., ComposeResponse[T]]
    __compose_names_by_type__: dict[typing.Any, str]

    def __init_subclass__(cls, abstract: bool = False, injection_hooks: tuple[InjectionHook, ...] = ()) -> None: ...

__all__ = ("Annotate", "Injection", "Node", "Queue")
