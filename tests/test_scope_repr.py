import pytest
import asyncio
from nodnod import Scope, Value, scalar_node


class TestScopeRepr:
    def test_empty_scope_repr(self):
        scope = Scope(detail="empty")
        # Clear the self-reference to make it truly empty for repr
        scope.clear()
        
        repr_str = repr(scope)
        assert "empty" in repr_str
        assert "(empty)" in repr_str
    
    def test_scope_repr_with_values(self):
        @scalar_node
        class TestNode:
            @classmethod
            def __compose__(cls) -> int:
                return 42
        
        scope = Scope(detail="test")
        scope.push(Value(TestNode, 42))
        
        repr_str = repr(scope)
        assert "test" in repr_str
        assert "TestNode" in repr_str
    
    @pytest.mark.asyncio
    async def test_scope_close_with_multiple_async_values(self):
        class AsyncValue1:
            def __init__(self):
                self.closed = False
            
            async def close(self):
                await asyncio.sleep(0.01)
                self.closed = True
        
        class AsyncValue2:
            def __init__(self):
                self.closed = False
            
            async def close(self):
                await asyncio.sleep(0.01) 
                self.closed = True
        
        scope = Scope(detail="async_test")
        obj1 = AsyncValue1()
        obj2 = AsyncValue2()
        
        # Use custom Value objects with async generators to trigger the gather path
        async def async_gen1():
            yield obj1
        
        async def async_gen2():
            yield obj2
        
        gen1 = async_gen1()
        await gen1.__anext__()
        gen2 = async_gen2()
        await gen2.__anext__()
        
        scope.push(Value(AsyncValue1, obj1, generator=gen1))
        scope.push(Value(AsyncValue2, obj2, generator=gen2))
        
        await scope.close()
        assert scope.is_closed