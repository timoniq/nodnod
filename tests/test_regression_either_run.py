"""Regression tests for the concurrent-either resolver and EventLoopAgent.run draining."""

import asyncio

import kungfu
import pytest

from nodnod import EventLoopAgent, Node, NodeError, Scope, scalar_node
from nodnod.agent.event_loop.coroutine import dependency_concurrent_either_coroutine
from nodnod.interface.either import ConcurrentEither


@pytest.mark.asyncio
async def test_concurrent_either_all_fail_collects_each_error_once():
    """A slow-failing branch must not make the loop busy-spin and duplicate the fast branch's
    error: each candidate is observed exactly once (regression: O(n^2) duplicate errors)."""

    async def fail_fast() -> kungfu.Result:
        return kungfu.Error(NodeError("fast"))

    async def fail_slow() -> kungfu.Result:
        await asyncio.sleep(0.02)
        return kungfu.Error(NodeError("slow"))

    deps = [asyncio.ensure_future(fail_fast()), asyncio.ensure_future(fail_slow())]
    result = await dependency_concurrent_either_coroutine(deps)

    assert kungfu.is_err(result)
    # Exactly two errors, not hundreds of duplicated fast-branch errors.
    assert len(result.error.from_many) == 2


@pytest.mark.asyncio
async def test_sequential_either_falls_back_to_nested_either_candidate():
    """A sequential-either fallback candidate that is itself an Either (here Option[B]) must be
    pushable: regression for AttributeError on the missing `__traverse__`."""

    @scalar_node
    class FailA(Node[int]):
        @classmethod
        def __compose__(cls) -> int:
            raise NodeError("A fails")

    @scalar_node
    class OkB(Node[int]):
        @classmethod
        def __compose__(cls) -> int:
            return 7

    @scalar_node
    class Consumer(Node[str]):
        @classmethod
        def __compose__(cls, value: FailA | kungfu.Option[OkB]) -> str:
            return f"got {value}"

    agent = EventLoopAgent.build({Consumer})

    async with Scope(detail="test") as scope:
        await agent.run(scope, {})
        result = scope.retrieve(Consumer)

    assert kungfu.is_some(result)
    assert "got" in result.unwrap().value


@pytest.mark.asyncio
async def test_concurrent_either_does_not_hang_on_blocking_loser():
    """The losing branch must be cancelled (not awaited to completion) once the winner resolves,
    so a loser that blocks indefinitely cannot hang run() — the canonical 'race the sources, take
    the fastest' pattern."""

    @scalar_node
    class FastWin(Node[int]):
        @classmethod
        async def __compose__(cls) -> int:
            return 1

    @scalar_node
    class BlockingLoser(Node[int]):
        @classmethod
        async def __compose__(cls) -> int:
            await asyncio.Event().wait()  # never completes
            return 2

    @scalar_node
    class Either(ConcurrentEither):
        __either__ = (FastWin, BlockingLoser)

    agent = EventLoopAgent.build({Either})

    async with Scope(detail="test") as scope:
        await asyncio.wait_for(agent.run(scope, {}), timeout=2.0)
        assert scope.retrieve(Either).unwrap().value == 1


@pytest.mark.asyncio
async def test_failed_run_still_tears_down_sibling_resources():
    """When a node fails, sibling tasks are drained before run() unwinds so their generators are
    cleaned by the scope rather than leaking to GC."""

    cleaned: list[str] = []

    @scalar_node
    class Boom(Node[int]):
        @classmethod
        async def __compose__(cls) -> int:
            raise NodeError("boom")

    @scalar_node
    class SlowResource(Node[int]):
        @classmethod
        async def __compose__(cls):
            try:
                await asyncio.sleep(0.02)
                yield 1
            finally:
                cleaned.append("sibling")

    agent = EventLoopAgent.build({Boom, SlowResource})

    with pytest.raises(NodeError):
        async with Scope(detail="test") as scope:
            await agent.run(scope, {})

    assert cleaned == ["sibling"]
