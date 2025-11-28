import typing

import kungfu
import pytest

from nodnod import Node
from nodnod.error import NodeBuildError
from nodnod.interface.union_node import create_union_node, get_none_node


class TestUnionNodesExtended:
    def test_get_none_node(self):
        none_node = get_none_node()
        assert issubclass(none_node, Node)
        assert none_node.__name__ == "NoneNode"
        assert none_node.__dependencies__ == set()

    def test_create_union_node_empty_args(self):
        # Create a union with no args to test the error case
        empty_union = typing.Union

        with pytest.raises(NodeBuildError, match="Union must have at least one type argument"):
            create_union_node(empty_union)

    def test_create_union_node_with_none_type(self):
        class TestNode(Node, abstract=True):
            __dependencies__ = set()
            __injections__ = set()

        TestNode.__type__ = TestNode

        # Union with None (Optional)
        optional_union = typing.Union[TestNode, type(None)]
        union_node = create_union_node(optional_union)

        assert issubclass(union_node, Node)
        # Should handle the None case
        assert hasattr(union_node, "__either__")

    def test_create_union_node_with_option_type(self):
        class TestNode(Node, abstract=True):
            __dependencies__ = set()
            __injections__ = set()

        TestNode.__type__ = TestNode
        # Union with Option type
        option_union = typing.Union[kungfu.Option[TestNode], int]
        union_node = create_union_node(option_union)

        assert issubclass(union_node, Node)
        assert hasattr(union_node, "__either__")

    def test_create_union_node_with_injected_types(self):
        # TODO
        pass
