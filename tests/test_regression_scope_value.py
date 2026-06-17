"""Regression tests for Scope teardown / merge semantics and Value generator cleanup."""

import inspect
import subprocess
import sys
import textwrap

import pytest

from nodnod import EventLoopAgent, Node, Scope, Value, scalar_node


def test_merge_child_value_shadows_parent():
    """merge() must resolve key conflicts child-first, like retrieve() (regression: parent
    clobbered child)."""
    parent = Scope(detail="parent")
    child = parent.create_child("child")
    parent.inject(int, "PARENT")
    child.inject(int, "CHILD")

    assert child.retrieve(int).unwrap().value == "CHILD"

    merged = child.merge()
    assert merged.retrieve(int).unwrap().value == "CHILD"
    # The synthetic Scope entry points at the merged scope, not an ancestor.
    assert merged[Scope].value is merged


def test_value_close_runs_post_yield_cleanup_for_single_yield():
    log: list[str] = []

    def gen():
        yield 1
        log.append("cleanup")

    g = gen()
    next(g)
    Value(int, 1, generator=g).close()

    assert log == ["cleanup"]


def test_value_close_finalizes_multi_yield_generator():
    """A generator that erroneously yields again must be force-closed (its finally run) instead
    of being left suspended for non-deterministic GC."""
    log: list[str] = []

    def gen():
        try:
            yield 1
            yield 2
        finally:
            log.append("closed")

    g = gen()
    next(g)
    Value(int, 1, generator=g).close()

    assert inspect.getgeneratorstate(g) == inspect.GEN_CLOSED
    assert log == ["closed"]


def test_close_collects_teardown_error_and_still_clears_scope():
    """A raising sync teardown must not abort the whole close(): the scope is still cleared and
    the error surfaces (regression: scope left non-empty and permanently un-closeable)."""

    def bad_gen():
        try:
            yield 1
        finally:
            raise RuntimeError("teardown boom")

    g = bad_gen()
    next(g)
    scope = Scope(detail="test")
    scope.push(Value(int, 1, generator=g))

    with pytest.raises(RuntimeError, match="teardown boom"):
        scope.close()

    assert scope.is_closed
    assert len(scope) == 0


@pytest.mark.asyncio
async def test_sync_exit_refuses_async_generator_cleanup():
    """`with scope` cannot await async-generator teardown, so it must refuse loudly instead of
    silently dropping the cleanup coroutine."""

    async def agen():
        yield 1

    g = agen()
    await g.__anext__()

    scope = Scope(detail="test")
    scope.push(Value(int, 1, generator=g))

    with pytest.raises(RuntimeError, match="async-generator"):
        with scope:
            pass

    await g.aclose()


@pytest.mark.asyncio
async def test_scope_closes_dependents_before_dependencies():
    """LIFO teardown: a dependent (inserted last) is closed before the dependencies it used."""
    order: list[str] = []

    @scalar_node
    class A(Node[int]):
        @classmethod
        async def __compose__(cls):
            try:
                yield 1
            finally:
                order.append("A")

    @scalar_node
    class B(Node[int]):
        @classmethod
        async def __compose__(cls):
            try:
                yield 2
            finally:
                order.append("B")

    @scalar_node
    class C(Node[int]):
        @classmethod
        async def __compose__(cls, a: A, b: B):
            try:
                yield a + b
            finally:
                order.append("C")

    agent = EventLoopAgent.build({C})

    async with Scope(detail="test") as scope:
        await agent.run(scope, {})

    assert order[0] == "C"
    assert set(order) == {"A", "B", "C"}


@pytest.mark.asyncio
async def test_scope_lifo_teardown_across_mixed_sync_and_async_generators():
    """Strict global LIFO must hold even when a sync-generator dependency was inserted before an
    async-generator dependent (regression: sync teardowns all ran before async ones)."""
    order: list[str] = []

    @scalar_node
    class Pool(Node[int]):
        @classmethod
        def __compose__(cls):  # synchronous generator dependency
            try:
                yield 1
            finally:
                order.append("Pool")

    @scalar_node
    class Worker(Node[int]):
        @classmethod
        async def __compose__(cls, pool: Pool):  # async generator dependent
            try:
                yield pool + 1
            finally:
                order.append("Worker")

    agent = EventLoopAgent.build({Worker})

    async with Scope(detail="test") as scope:
        await agent.run(scope, {})

    # The dependent (Worker) is torn down before the dependency (Pool) it used.
    assert order == ["Worker", "Pool"]


def test_scope_link_validation_runs_under_optimized_mode():
    """The mapped-scope linkage check is a correctness invariant and must run even under -O,
    where __debug__ is False (regression: guarded by `if __debug__`)."""
    code = textwrap.dedent(
        """
        from nodnod import Node, Scope
        from nodnod.scope import validate_local_scope_is_linked_to_node_scopes
        from nodnod.error import NodeError

        class N(Node):
            @classmethod
            def __compose__(cls) -> int:
                return 1

        s1 = Scope(detail="a")
        s2 = Scope(detail="b")
        try:
            validate_local_scope_is_linked_to_node_scopes(s1, {N: s2})
        except NodeError:
            print("RAISED")
        else:
            print("NOT_RAISED")
        """
    )
    out = subprocess.run([sys.executable, "-O", "-c", code], capture_output=True, text=True)
    assert "RAISED" in out.stdout, out.stderr
