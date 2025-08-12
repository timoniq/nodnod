from nodnod import Node, scalar_node


class TestNodeRepr:
    def test_node_repr(self):
        @scalar_node
        class TestNode:
            @classmethod
            def __compose__(cls) -> int:
                return 42
        
        node = TestNode()
        repr_str = repr(node)
        assert "TestNode" in repr_str
        assert "<node" in repr_str
    
    def test_dummy_compose_function(self):
        from nodnod.node import dummy_compose
        
        class TestClass:
            pass
        
        # dummy_compose is a classmethod, so call it on a class that has it
        # Actually, we need to test the function directly since it's decorated
        instance = dummy_compose.__func__(TestClass)
        assert isinstance(instance, TestClass)