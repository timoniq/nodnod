import kungfu
import pytest

from nodnod.node import Node
from nodnod.error import NodeBuildError
from nodnod.interface.create_result_node import create_result_node


def test_create_result_node_build_error():
    with pytest.raises(NodeBuildError, match=r"`int` does not have a `__compose__` method"):
        create_result_node(kungfu.Result[int, ValueError])


def test_create_result_node_different_types():
    class StrNode(Node):
        @classmethod
        def __compose__(cls) -> str:
            ...

    class ListNode(Node):
        @classmethod
        def __compose__(cls) -> list[int]:
            ...

    result_node1 = create_result_node(kungfu.Result[StrNode, RuntimeError])
    result_node2 = create_result_node(kungfu.Result[ListNode, TypeError])

    assert result_node1.__from_node__ is StrNode
    assert result_node1.__error__ is RuntimeError
    assert result_node2.__from_node__ is ListNode
    assert result_node2.__error__ is TypeError

def test_create_result_node_no_type_args():
    with pytest.raises(NodeBuildError) as exc_info:
        create_result_node(kungfu.Result)  # type: ignore

    assert "Result must have specified type arguments" in str(exc_info.value)


def test_create_result_node_caching():
    class IntNode(Node):
        @classmethod
        def __compose__(cls) -> str:
            ...

    result_node1 = create_result_node(kungfu.Result[IntNode, ValueError])
    result_node2 = create_result_node(kungfu.Result[IntNode, ValueError])
    assert result_node1 is result_node2
