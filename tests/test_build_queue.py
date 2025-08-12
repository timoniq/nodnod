import pytest
from nodnod import scalar_node, Node
from nodnod.builder.build_queue import build_queue, traverse_all
from nodnod.builder.validate_graph import validate_no_circular_dependency


class TestBuildQueue:
    def test_build_queue_simple(self):
        @scalar_node
        class SimpleNode:
            @classmethod
            def __compose__(cls) -> int:
                return 42
        
        queue = build_queue(SimpleNode, [])
        assert SimpleNode in queue
    
    def test_traverse_all(self):
        @scalar_node
        class NodeA:
            @classmethod
            def __compose__(cls) -> int:
                return 1
        
        @scalar_node
        class NodeB:
            @classmethod
            def __compose__(cls, a: NodeA) -> int:
                return a * 2
        
        nodes = {NodeA, NodeB}
        traversed = traverse_all(nodes)
        
        assert NodeA in traversed
        assert NodeB in traversed
    
    def test_validate_no_circular_dependency_valid(self):
        @scalar_node
        class ValidNode:
            @classmethod
            def __compose__(cls) -> int:
                return 42
        
        # Should not raise for valid node
        try:
            validate_no_circular_dependency(ValidNode, [])
        except Exception:
            pytest.fail("validate_no_circular_dependency raised unexpectedly")
    
    def test_validate_circular_dependency_detected(self):
        from nodnod.error import NodeBuildError
        
        @scalar_node
        class NodeA:
            @classmethod  
            def __compose__(cls) -> int:
                return 42
        
        @scalar_node
        class NodeB:
            @classmethod
            def __compose__(cls, a: NodeA) -> int:
                return a
        
        # Manually create circular dependency by modifying NodeA's dependencies
        NodeA.__dependencies__ = {NodeB}
        
        with pytest.raises(NodeBuildError):
            validate_no_circular_dependency(NodeA, [])