import kungfu
import pytest

from nodnod import Node
from nodnod.error import NodeBuildError
from nodnod.interface.option_node import create_option_node


class TestOptionNodeExtended:
    def test_create_option_node_no_args(self):
        with pytest.raises(NodeBuildError, match="Option must have exactly one type argument"):
            empty_option = kungfu.Option
            create_option_node(empty_option)

    def test_create_option_node_with_non_node_type(self):
        with pytest.raises(NodeBuildError, match="`int` does not have a `__compose__` method"):
            create_option_node(kungfu.Option[int])

    def test_create_option_node_with_node_type(self):
        class TestNode(Node, abstract=True):
            __dependencies__ = set()
            __injections__ = set()

        TestNode.__type__ = TestNode

        option_type = kungfu.Option[TestNode]
        option_node = create_option_node(option_type)

        assert issubclass(option_node, Node)
        assert list(option_node.__dependencies__)[0].__dependencies__.pop() is TestNode
        assert option_node.__injections__ == set()
