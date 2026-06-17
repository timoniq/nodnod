import secrets
import types
import typing
from collections import OrderedDict

from kungfu.library.monad.option import NOTHING, Option, Some

from nodnod.error import NodeError
from nodnod.node import Node
from nodnod.utils.aio import awaitable_noop
from nodnod.value import Value

type AnyType = typing.Any


def _raise_teardown_errors(errors: list[BaseException]) -> typing.NoReturn:
    if len(errors) == 1:
        raise errors[0]
    raise NodeError(
        "errors occurred during scope teardown",
        from_many=[error if isinstance(error, NodeError) else NodeError(repr(error)) for error in errors],
    )


class Scope(OrderedDict[AnyType, Value]):
    def __init__(self, prev: "Scope | None" = None, detail: str | None = None) -> None:
        self.prev = prev
        self.detail = detail or secrets.token_hex(5)
        self.is_closed = False

        super().__init__([(Scope, Value(Scope, self))])

    def __repr__(self) -> str:
        return f"Scope {self.detail} " + (", ".join(f"{node_t.__name__}: {value!r}" for node_t, value in self.items() if value.value is not self) if self else "(empty)")

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

        # LIFO teardown: dependents are inserted after the dependencies they consume, so
        # closing in reverse insertion order tears down a dependent before its dependencies.
        values = list(reversed(self.values()))
        self.clear()

        if any(isinstance(value.generator, types.AsyncGeneratorType) for value in values):
            # Some teardown is asynchronous: process every value sequentially in a single
            # coroutine so the strict reverse-insertion order holds across mixed sync/async
            # generators (running sync closes first then async would invert dependency order).
            return self._close_values_async(values)

        errors: list[BaseException] = []
        for value in values:
            try:
                value.close()
            except Exception as error:  # noqa: BLE001 - never abort teardown; collect and continue
                errors.append(error)
        if errors:
            _raise_teardown_errors(errors)
        return awaitable_noop()

    async def _close_values_async(self, values: list[Value]) -> None:
        errors: list[BaseException] = []
        for value in values:
            try:
                result = value.close()
                if not isinstance(result, awaitable_noop):
                    await result
            except Exception as error:  # noqa: BLE001
                errors.append(error)
        if errors:
            _raise_teardown_errors(errors)

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
        if self.is_closed:
            return

        # Async-generator teardown needs an event loop; a synchronous `with` cannot await it.
        # Refuse loudly instead of silently dropping the cleanup coroutine (leaking the resource).
        if any(isinstance(value.generator, types.AsyncGeneratorType) for value in self.values()):
            raise RuntimeError(
                "Scope holds async-generator dependencies whose teardown requires an event "
                "loop; use `async with scope` (or `await scope.close()`) instead of `with scope`.",
            )

        self.close()

    async def __aenter__(self) -> typing.Self:
        return self

    async def __aexit__(self, *_: typing.Any) -> None:
        if not self.is_closed:
            await self.close()

    def merge(self) -> "Scope":
        scope = Scope(detail="merge")

        chain: list[Scope] = []
        part: Scope | None = self
        while part is not None:
            chain.append(part)
            part = part.prev

        # Update from the root ancestor down to self, so that on a key conflict the nearest
        # (child) scope wins — matching retrieve()'s child-first resolution order.
        for part in reversed(chain):
            scope.update(part)

        # Keep the synthetic Scope->self entry pointing at the merged scope itself.
        scope[Scope] = Value(Scope, scope)
        return scope

    def inject(self, t: AnyType, value: typing.Any) -> None:
        self[t] = Value(t, value)


def validate_local_scope_is_linked_to_node_scopes(local_scope: Scope, node_scopes: dict[type[Node], Scope]) -> None:
    # This is a correctness invariant (a detached mapped scope silently sends values to an
    # unreachable scope), so it must run unconditionally — not only when `__debug__` is true.
    for node, node_scope in node_scopes.items():
        if not local_scope.has_parent(node_scope):
            raise NodeError(f"`{node.__name__}`'s scope ({node_scope.detail}) is not a parent of local scope ({local_scope.detail})")


__all__ = ("Scope", "validate_local_scope_is_linked_to_node_scopes")
