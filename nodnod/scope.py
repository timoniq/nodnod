import asyncio
import secrets
import typing
from collections import OrderedDict

from kungfu.library.monad.option import NOTHING, Option, Some

from nodnod.error import NodeError
from nodnod.node import Node
from nodnod.utils.aio import awaitable_noop
from nodnod.value import Value

type AnyType = typing.Any


class Scope(OrderedDict[AnyType, Value]):
    def __init__(self, prev: "Scope | None" = None, detail: str | None = None) -> None:
        self.prev = prev
        self.detail = detail or secrets.token_hex(5)
        self.is_closed = False

        super().__init__([(Scope, Value(Scope, self))])

    def __repr__(self) -> str:
        return f"Scope {self.detail} " + (
            ", ".join(f"{node_t.__name__}: {value!r}" for node_t, value in self.items() if value.value is not self)
            if self
            else "(empty)"
        )

    def retrieve(self, key: AnyType) -> Option[Value]:
        if key not in self:
            if not self.prev:
                return NOTHING
            return self.prev.retrieve(key)
        return Some(self[key])

    def push(self, value: Value) -> None:
        self[value.cls] = value

    def close(self) -> typing.Awaitable[typing.Any]:
        if self.is_closed:
            raise RuntimeError("Scope has already been closed")

        self.is_closed = True
        coros = []

        for value in self.values():
            result = value.close()
            if not isinstance(result, awaitable_noop):
                coros.append(result)

        self.clear()

        if not coros:
            return awaitable_noop()

        return asyncio.gather(*coros)

    def has_parent(self, parent: "Scope") -> bool:
        candidate = self.prev
        while candidate is not None:
            if candidate is parent:
                return True
            candidate = candidate.prev
        return False

    def create_child(self, detail: str | None = None) -> "Scope":
        return Scope(prev=self, detail=detail)

    def __enter__(self) -> typing.Self:
        return self

    def __exit__(self, *_: typing.Any) -> None:
        if not self.is_closed:
            self.close()

    async def __aenter__(self) -> typing.Self:
        return self

    async def __aexit__(self, *_: typing.Any) -> None:
        if not self.is_closed:
            await self.close()

    def merge(self) -> "Scope":
        scope = Scope(detail="merge")
        part = self
        while part is not None:
            scope.update(part)
            part = part.prev
        return scope

    def inject(self, t: AnyType, value: typing.Any) -> None:
        self[t] = Value(t, value)


def validate_local_scope_is_linked_to_node_scopes(
    local_scope: Scope, node_scopes: dict[type[Node], Scope]
) -> None:
    if __debug__:
        for node, node_scope in node_scopes.items():
            if not local_scope.has_parent(node_scope):
                raise NodeError(
                    f"`{node.__name__}`'s scope ({node_scope.detail}) is not a parent of local scope ({local_scope.detail})"
                )


__all__ = ("Scope", "validate_local_scope_is_linked_to_node_scopes")
