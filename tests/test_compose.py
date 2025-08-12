import pytest
import asyncio
import fntypes
from nodnod.compose import compose_node, initialize_node
from nodnod import Node, scalar_node, NodeError, Scope, Value


class TestCompose:
    @pytest.mark.asyncio
    async def test_compose_simple_node(self):
        @scalar_node
        class SimpleNode:
            @classmethod
            def __compose__(cls) -> int:
                return 42
        
        scope = Scope(detail="test")
        result = await compose_node(SimpleNode, scope, scope)
        
        assert fntypes.is_ok(result)
        value = result.unwrap()
        assert value.value == 42
    
    @pytest.mark.asyncio
    async def test_compose_node_with_error(self):
        @scalar_node
        class ErrorNode:
            @classmethod
            def __compose__(cls) -> int:
                raise NodeError("Test error")
        
        scope = Scope(detail="test")
        result = await compose_node(ErrorNode, scope, scope)
        
        assert fntypes.is_err(result)
        assert isinstance(result.error, NodeError)
    
    @pytest.mark.asyncio
    async def test_compose_cached_node(self):
        @scalar_node
        class CachedNode:
            @classmethod
            def __compose__(cls) -> int:
                return 99
        
        scope = Scope(detail="test")
        # Pre-populate the scope
        scope.push(Value(CachedNode, 123))
        
        result = await compose_node(CachedNode, scope, scope)
        
        assert fntypes.is_ok(result)
        # Should return cached value, not newly computed
        assert result.unwrap().value == 123
    
    @pytest.mark.asyncio
    async def test_initialize_node_simple_value(self):
        @scalar_node
        class TestNode:
            @classmethod
            def __compose__(cls) -> int:
                return 42
        
        value = await initialize_node(TestNode, 42)
        assert isinstance(value, Value)
        assert value.cls == TestNode
        assert value.value == 42
    
    @pytest.mark.asyncio
    async def test_initialize_node_awaitable(self):
        @scalar_node
        class TestNode:
            @classmethod
            async def __compose__(cls) -> str:
                return "async"
        
        async def async_value():
            return "awaitable_result"
        
        value = await initialize_node(TestNode, async_value())
        assert value.value == "awaitable_result"
    
    @pytest.mark.asyncio
    async def test_initialize_node_with_sync_generator(self):
        @scalar_node
        class TestNode:
            @classmethod
            def __compose__(cls) -> int:
                return 42
        
        def gen():
            yield 123
        
        generator = gen()
        value = await initialize_node(TestNode, generator)
        assert value.value == 123
        assert value.generator is generator
    
    @pytest.mark.asyncio
    async def test_initialize_node_with_async_generator(self):
        @scalar_node
        class TestNode:
            @classmethod
            def __compose__(cls) -> int:
                return 42
        
        async def agen():
            yield 456
        
        generator = agen()
        value = await initialize_node(TestNode, generator)
        assert value.value == 456
        assert value.generator is generator