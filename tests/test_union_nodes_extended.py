import sys
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
        empty_union = typing.Union

        with pytest.raises(NodeBuildError, match="Union must have at least one type argument"):
            create_union_node(empty_union)

    def test_create_union_node_with_none_type(self):
        class TestNode(Node, abstract=True):
            __dependencies__ = set()
            __injections__ = set()

        TestNode.__type__ = TestNode

        optional_union = typing.Union[TestNode, type(None)]
        union_node = create_union_node(optional_union)

        assert issubclass(union_node, Node)
        assert hasattr(union_node, "__either__")

    def test_create_union_node_with_option_type(self):
        class TestNode(Node):
            @classmethod
            def __compose__(cls) -> None:
                ...

        class IntNode(Node):
            @classmethod
            def __compose__(cls) -> int:
                ...

        union_node = create_union_node(typing.Union[IntNode, kungfu.Option[TestNode]])

        assert issubclass(union_node, Node)
        assert hasattr(union_node, "__either__")

    def test_create_union_node_with_result_type(self):
        class TestNode(Node):
            @classmethod
            def __compose__(cls) -> int:
                ...

        union_node = create_union_node(typing.Union[TestNode, kungfu.Result[TestNode, ValueError]])

        assert issubclass(union_node, Node)
        assert hasattr(union_node, "__either__")

    def test_create_union_node_with_composable_and_injected_types(self):
        class ComposableClass:
            @classmethod
            def __compose__(cls) -> int:
                ...

        union_node = create_union_node(typing.Union[ComposableClass, int])

        assert issubclass(union_node, Node)
        assert hasattr(union_node, "__either__")
        assert union_node.__injections__ == {int}
