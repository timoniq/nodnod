import pytest
import asyncio
import fntypes
from nodnod import Node, Scope, EventLoopAgent, scalar_node, DataNode, NodeError
from nodnod.interface.scalar import scalar_node
import dataclasses


class TestBasicNode:
    def test_node_creation(self):
        @scalar_node
        class SimpleNode:
            @classmethod
            def __compose__(cls) -> int:
                return 42
        
        assert issubclass(SimpleNode, Node)
    
    def test_node_with_dependencies(self):
        @scalar_node
        class NodeA:
            @classmethod
            def __compose__(cls) -> int:
                return 10
        
        @scalar_node
        class NodeB:
            @classmethod
            def __compose__(cls, a: NodeA) -> int:
                return a * 2
        
        assert NodeA in NodeB.__dependencies__
    
    def test_scalar_node_decorator_on_function(self):
        @scalar_node
        def my_function() -> str:
            return "hello"
        
        assert issubclass(my_function, Node)


class TestDataNode:
    def test_data_node_creation(self):
        @dataclasses.dataclass
        class TestData(DataNode):
            value: int
            name: str
            
            @classmethod
            def __compose__(cls):
                return cls(value=42, name="test")
        
        assert issubclass(TestData, DataNode)
        assert issubclass(TestData, Node)


class TestScope:
    def test_scope_creation(self):
        scope = Scope(detail="test")
        assert scope.detail == "test"
        assert not scope.is_closed
    
    def test_scope_push_retrieve(self):
        from nodnod import Value
        
        scope = Scope()
        value = Value(int, 42)
        scope.push(value)
        
        retrieved = scope.retrieve(int)
        assert fntypes.is_some(retrieved)
        assert retrieved.unwrap().value == 42
    
    def test_scope_hierarchy(self):
        from nodnod import Value
        
        parent = Scope(detail="parent")
        child = parent.create_child("child")
        
        parent_value = Value(str, "parent_value")
        parent.push(parent_value)
        
        retrieved = child.retrieve(str)
        assert fntypes.is_some(retrieved)
        assert retrieved.unwrap().value == "parent_value"
    
    def test_scope_has_parent(self):
        parent = Scope(detail="parent")
        child = parent.create_child("child")
        grandchild = child.create_child("grandchild")
        
        assert grandchild.has_parent(parent)
        assert grandchild.has_parent(child)
        assert not child.has_parent(grandchild)
    
    @pytest.mark.asyncio
    async def test_scope_async_context(self):
        scope = Scope(detail="test")
        
        async with scope:
            assert not scope.is_closed
        
        assert scope.is_closed


class TestEventLoopAgent:
    @pytest.mark.asyncio
    async def test_simple_agent_execution(self):
        @scalar_node
        class SimpleNode:
            @classmethod
            def __compose__(cls) -> int:
                return 100
        
        agent = EventLoopAgent.build({SimpleNode})
        scope = Scope(detail="test")
        
        async with scope:
            await agent.run(local_scope=scope, mapped_scopes={})
            result = scope.retrieve(SimpleNode)
            assert fntypes.is_some(result)
            assert result.unwrap().value == 100
    
    @pytest.mark.asyncio
    async def test_agent_with_dependencies(self):
        @scalar_node
        class NodeA:
            @classmethod
            def __compose__(cls) -> int:
                return 10
        
        @scalar_node
        class NodeB:
            @classmethod
            def __compose__(cls, a: NodeA) -> int:
                return a * 3
        
        agent = EventLoopAgent.build({NodeB})
        scope = Scope(detail="test")
        
        async with scope:
            await agent.run(local_scope=scope, mapped_scopes={})
            
            result_a = scope.retrieve(NodeA)
            result_b = scope.retrieve(NodeB)
            
            assert fntypes.is_some(result_a)
            assert fntypes.is_some(result_b)
            assert result_a.unwrap().value == 10
            assert result_b.unwrap().value == 30
    
    @pytest.mark.asyncio
    async def test_agent_with_async_compose(self):
        @scalar_node
        class AsyncNode:
            @classmethod
            async def __compose__(cls) -> str:
                await asyncio.sleep(0.01)
                return "async_result"
        
        agent = EventLoopAgent.build({AsyncNode})
        scope = Scope(detail="test")
        
        async with scope:
            await agent.run(local_scope=scope, mapped_scopes={})
            result = scope.retrieve(AsyncNode)
            assert fntypes.is_some(result)
            assert result.unwrap().value == "async_result"


class TestNodeError:
    @pytest.mark.asyncio
    async def test_node_error_propagation(self):
        @scalar_node
        class FailingNode:
            @classmethod
            def __compose__(cls) -> int:
                raise NodeError("Test error")
        
        agent = EventLoopAgent.build({FailingNode})
        scope = Scope(detail="test")
        
        async with scope:
            with pytest.raises(NodeError, match="Test error"):
                await agent.run(local_scope=scope, mapped_scopes={})