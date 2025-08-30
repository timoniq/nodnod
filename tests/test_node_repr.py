import pytest

from nodnod import Node


class TestNodeRepr:
    def test_node_repr(self):
        class TestNode(Node, abstract=True):
            __dependencies__ = set()
            __injections__ = set()

        TestNode.__type__ = TestNode

        node = TestNode()
        repr_str = repr(node)
        assert "`TestNode`" in repr_str
        assert "<node" in repr_str

    def test_dummy_compose_function(self):
        from nodnod.node import dummy_compose

        class TestClass:
            pass

        # dummy_compose is a classmethod, so call it on a class that has it
        # Actually, we need to test the function directly since it's decorated
        with pytest.raises(
            RuntimeError, match="`TestClass` does not provide `__compose__`. Maybe it should be abstract=True?"
        ):
            dummy_compose.__func__(TestClass)
