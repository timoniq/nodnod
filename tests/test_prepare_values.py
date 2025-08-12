import pytest
from nodnod.utils.prepare_values import prepare_values
from nodnod import Scope, Value, scalar_node


class TestPrepareValues:
    def test_prepare_values_with_scalar_nodes(self):
        @scalar_node
        class TestNode:
            @classmethod
            def __compose__(cls) -> int:
                return 42
        
        scope = Scope(detail="test")
        scope.push(Value(TestNode, 42))
        
        result = prepare_values(scope)
        assert TestNode in result
        assert result[TestNode] == 42
    
    def test_prepare_values_with_non_scalar_nodes(self):
        from nodnod import Node
        
        class NonScalarNode(Node):
            pass
        
        scope = Scope(detail="test")
        node_instance = NonScalarNode()
        scope.push(Value(NonScalarNode, node_instance))
        
        result = prepare_values(scope)
        assert NonScalarNode in result
        assert result[NonScalarNode] is node_instance
    
    def test_prepare_values_empty_scope(self):
        scope = Scope(detail="empty")
        result = prepare_values(scope)
        # Should only contain Scope itself
        assert len(result) == 1
        assert Scope in result