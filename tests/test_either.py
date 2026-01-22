import kungfu
import pytest

from nodnod import EventLoopAgent, NodeError, Scope, scalar_node
from nodnod.interface.either import ConcurrentEither, SequentialEither


class TestSequentialEither:
    @pytest.mark.asyncio
    async def test_sequential_either_success_first(self):
        @scalar_node
        class SuccessNode:
            @classmethod
            def __compose__(cls) -> int:
                return 42

        @scalar_node
        class FailNode:
            @classmethod
            def __compose__(cls) -> int:
                raise NodeError("Should not be called")

        @scalar_node
        class TestEither(SequentialEither):
            __either__ = (FailNode, SuccessNode)

        agent = EventLoopAgent.build({TestEither})
        scope = Scope(detail="test")

        async with scope:
            await agent.run(local_scope=scope, mapped_scopes={})
            result = scope.retrieve(TestEither)
            assert kungfu.is_some(result)
            assert result.unwrap().value == 42

    @pytest.mark.asyncio
    async def test_sequential_either_fallback(self):
        @scalar_node
        class FailNode:
            @classmethod
            def __compose__(cls) -> int:
                raise NodeError("First fails")

        @scalar_node
        class SuccessNode:
            @classmethod
            def __compose__(cls) -> int:
                return 99

        @scalar_node
        class TestEither(SequentialEither):
            __either__ = (FailNode, SuccessNode)

        agent = EventLoopAgent.build({TestEither})
        scope = Scope(detail="test")

        async with scope:
            await agent.run(local_scope=scope, mapped_scopes={})
            result = scope.retrieve(TestEither)
            assert kungfu.is_some(result)
            assert result.unwrap().value == 99


class TestConcurrentEither:
    @pytest.mark.asyncio
    async def test_concurrent_either(self):
        @scalar_node
        class FirstNode:
            @classmethod
            def __compose__(cls) -> int:
                return 100

        @scalar_node
        class SecondNode:
            @classmethod
            def __compose__(cls) -> int:
                return 200

        @scalar_node
        class TestEither(ConcurrentEither):
            __either__ = (FirstNode, SecondNode)

        agent = EventLoopAgent.build({TestEither})
        scope = Scope(detail="test")

        async with scope:
            await agent.run(local_scope=scope, mapped_scopes={})
            result = scope.retrieve(TestEither)
            assert kungfu.is_some(result)
            assert result.unwrap().value in (100, 200)
