import asyncio
from datetime import timedelta
from unittest.mock import Mock

import pytest

from nodnod import EventLoopAgent, Node, Scope, scalar_node
from nodnod.interface.cache import cache


class TestCache:
    @pytest.mark.asyncio
    async def test_cache_sync_function_direct(self):
        call_counter = Mock()

        @cache(seconds=1)
        @scalar_node
        class SyncNode:
            @classmethod
            def __compose__(cls) -> int:
                call_counter()
                return 42

        result1 = await SyncNode.__compose__()
        assert result1 == 42
        assert call_counter.call_count == 1

        result2 = await SyncNode.__compose__()
        assert result2 == 42
        assert call_counter.call_count == 1

    @pytest.mark.asyncio
    async def test_cache_async_function_direct(self):
        call_counter = Mock()

        @cache(seconds=1)
        @scalar_node
        class AsyncNode:
            @classmethod
            async def __compose__(cls) -> str:
                call_counter()
                await asyncio.sleep(0.01)
                return "async_result"

        result1 = await AsyncNode.__compose__()
        assert result1 == "async_result"
        assert call_counter.call_count == 1

        result2 = await AsyncNode.__compose__()
        assert result2 == "async_result"
        assert call_counter.call_count == 1

    @pytest.mark.asyncio
    async def test_cache_sync_generator_direct(self):
        call_counter = Mock()

        @cache(seconds=1)
        @scalar_node
        class SyncGenNode:
            @classmethod
            def __compose__(cls):
                call_counter()
                yield 100

        result1 = await SyncGenNode.__compose__()
        assert result1 == 100
        assert call_counter.call_count == 1

        result2 = await SyncGenNode.__compose__()
        assert result2 == 100
        assert call_counter.call_count == 1

    @pytest.mark.asyncio
    async def test_cache_async_generator_direct(self):
        call_counter = Mock()

        @cache(seconds=1)
        @scalar_node
        class AsyncGenNode:
            @classmethod
            async def __compose__(cls):
                call_counter()
                await asyncio.sleep(0.01)
                yield 200

        result1 = await AsyncGenNode.__compose__()
        assert result1 == 200
        assert call_counter.call_count == 1

        result2 = await AsyncGenNode.__compose__()
        assert result2 == 200
        assert call_counter.call_count == 1

    @pytest.mark.asyncio
    async def test_cache_expiration_direct(self):
        call_counter = Mock()

        @cache(milliseconds=50)
        @scalar_node
        class ExpiringNode:
            @classmethod
            def __compose__(cls) -> int:
                call_counter()
                return 999

        result1 = await ExpiringNode.__compose__()
        assert result1 == 999
        assert call_counter.call_count == 1

        result2 = await ExpiringNode.__compose__()
        assert result2 == 999
        assert call_counter.call_count == 1

        await asyncio.sleep(0.1)

        result3 = await ExpiringNode.__compose__()
        assert result3 == 999
        assert call_counter.call_count == 2

    @pytest.mark.asyncio
    async def test_cache_different_values_direct(self):
        counter = [0]

        @cache(seconds=1)
        @scalar_node
        class CounterNode:
            @classmethod
            def __compose__(cls) -> int:
                counter[0] += 1
                return counter[0]

        result1 = await CounterNode.__compose__()
        assert result1 == 1

        result2 = await CounterNode.__compose__()
        assert result2 == 1
        assert counter[0] == 1

    @pytest.mark.asyncio
    async def test_cache_multiple_agent_runs(self):
        call_counter = Mock()

        @cache(seconds=1)
        @scalar_node
        class CachedNode:
            @classmethod
            def __compose__(cls) -> int:
                call_counter()
                return 555

        agent = EventLoopAgent.build({CachedNode})

        scope1 = Scope(detail="test1")
        async with scope1:
            await agent.run(local_scope=scope1, mapped_scopes={})
            result1 = scope1.retrieve(CachedNode)
            assert result1.unwrap().value == 555

        scope2 = Scope(detail="test2")
        async with scope2:
            await agent.run(local_scope=scope2, mapped_scopes={})
            result2 = scope2.retrieve(CachedNode)
            assert result2.unwrap().value == 555

        assert call_counter.call_count == 1

    @pytest.mark.asyncio
    async def test_cache_ignores_argument_changes(self):
        @scalar_node
        class NodeA:
            @classmethod
            def __compose__(cls) -> int:
                return 10  # pragma: no cover

        @cache(seconds=1)
        @scalar_node
        class NodeB:
            @classmethod
            def __compose__(cls, a: NodeA) -> int:
                return a * 2

        result1 = await NodeB.__compose__(10)
        assert result1 == 20

        result2 = await NodeB.__compose__(99)
        assert result2 == 20

    @pytest.mark.asyncio
    async def test_cache_expiration_with_agent(self):
        call_counter = Mock()

        @cache(milliseconds=50)
        @scalar_node
        class ExpiringNode:
            @classmethod
            def __compose__(cls) -> int:
                call_counter()
                return 777

        agent = EventLoopAgent.build({ExpiringNode})

        scope1 = Scope(detail="test1")
        async with scope1:
            await agent.run(local_scope=scope1, mapped_scopes={})
            assert call_counter.call_count == 1

        scope2 = Scope(detail="test2")
        async with scope2:
            await agent.run(local_scope=scope2, mapped_scopes={})
            assert call_counter.call_count == 1

        await asyncio.sleep(0.1)

        scope3 = Scope(detail="test3")
        async with scope3:
            await agent.run(local_scope=scope3, mapped_scopes={})
            assert call_counter.call_count == 2

    def test_cache_decorator_on_non_composable(self):
        with pytest.raises(RuntimeError, match="cache decorator can only be used with a composable class"):
            @cache(seconds=1)
            class RegularClass:
                pass

    def test_cache_with_zero_time(self):
        with pytest.raises(RuntimeError, match="cache time must be greater than 0"):
            @cache(seconds=0)
            @scalar_node
            class ZeroTimeNode:
                @classmethod
                def __compose__(cls) -> int:
                    return 1  # pragma: no cover

    def test_cache_with_negative_time(self):
        with pytest.raises(RuntimeError, match="cache time must be greater than 0"):
            @cache(seconds=-1)
            @scalar_node
            class NegativeTimeNode:
                @classmethod
                def __compose__(cls) -> int:
                    return 1  # pragma: no cover

    def test_cache_inherits_timedelta(self):
        c = cache(seconds=10, milliseconds=500)
        assert isinstance(c, timedelta)
        assert c.total_seconds() == 10.5

    @pytest.mark.asyncio
    async def test_cache_preserves_node_type(self):
        @cache(seconds=1)
        @scalar_node
        class TestNode:
            @classmethod
            def __compose__(cls) -> int:
                return 42  # pragma: no cover

        assert issubclass(TestNode, Node)
        assert TestNode.__name__ == "Node:TestNode"
