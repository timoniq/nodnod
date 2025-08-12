import pytest
import asyncio
import fntypes
from nodnod import Node, Scope, EventLoopAgent, scalar_node, NodeError
from nodnod.interface.either import SequentialEither, ConcurrentEither


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
            __either__ = (SuccessNode, FailNode)
        
        agent = EventLoopAgent.build({TestEither})
        scope = Scope(detail="test")
        
        async with scope:
            await agent.run(local_scope=scope, mapped_scopes={})
            result = scope.retrieve(TestEither)
            assert fntypes.is_some(result)
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
            assert fntypes.is_some(result)
            assert result.unwrap().value == 99


class TestConcurrentEither:
    @pytest.mark.asyncio
    async def test_concurrent_either(self):
        @scalar_node
        class SlowNode:
            @classmethod
            async def __compose__(cls) -> int:
                await asyncio.sleep(0.1)
                return 100
        
        @scalar_node
        class FastNode:
            @classmethod
            def __compose__(cls) -> int:
                return 200
        
        @scalar_node
        class TestEither(ConcurrentEither):
            __either__ = (SlowNode, FastNode)
        
        agent = EventLoopAgent.build({TestEither})
        scope = Scope(detail="test")
        
        async with scope:
            await agent.run(local_scope=scope, mapped_scopes={})
            result = scope.retrieve(TestEither)
            assert fntypes.is_some(result)
            # Should get the fast result
            assert result.unwrap().value == 200