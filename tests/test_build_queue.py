import pytest

from nodnod.builder.build_queue import build_queue, traverse_all
from nodnod.builder.validate_graph import validate_no_circular_dependency
from nodnod.node import Node


class TestBuildQueue:
    def test_build_queue_simple(self):
        class SimpleNode(Node):
            pass

        queue = build_queue(SimpleNode, [])
        assert SimpleNode in queue

    def test_build_queue_dependency_in_queue(self):
        class A(Node, abstract=True):
            __dependencies__ = set()
            __injections__ = set()

        class B(Node, abstract=True):
            __dependencies__ = {A}
            __injections__ = set()

        queue = build_queue(B, [A])
        assert A in queue
        assert B in queue

    def test_traverse_all(self):
        class NodeA(Node, abstract=True):
            __dependencies__ = set()
            __injections__ = set()

        class NodeB(Node, abstract=True):
            __dependencies__ = {NodeA}
            __injections__ = set()

        nodes = {NodeA, NodeB}
        traversed = traverse_all(nodes)

        assert NodeA in traversed
        assert NodeB in traversed

    def test_validate_no_circular_dependency_valid(self):
        class ValidNode(Node, abstract=True):
            __dependencies__ = set()
            __injections__ = set()

        # Should not raise for valid node
        validate_no_circular_dependency(ValidNode, [])

    def test_validate_circular_dependency_detected(self):
        from nodnod.error import NodeBuildError

        class NodeA(Node, abstract=True):
            __dependencies__ = set()
            __injections__ = set()

        class NodeB(Node, abstract=True):
            __dependencies__ = {NodeA}
            __injections__ = set()

        # Manually create circular dependency by modifying NodeA's dependencies
        NodeA.__dependencies__.add(NodeB)

        with pytest.raises(NodeBuildError):
            validate_no_circular_dependency(NodeA, [])
