import kungfu
import pytest

from nodnod.error import NodeBuildError
from nodnod.interface.create_result_node import create_result_node
from nodnod.interface.result_node import ResultNode


def test_create_result_node_success():
    result_node = create_result_node(kungfu.Result[int, ValueError])

    assert issubclass(result_node, ResultNode)
    assert result_node.__name__ == "ResultNode[int, ValueError]"
    assert result_node.__from_node__ is int
    assert result_node.__error__ is ValueError
    assert result_node.__type__ == kungfu.Result[int, ValueError]


def test_create_result_node_different_types():
    result_node1 = create_result_node(kungfu.Result[str, RuntimeError])
    result_node2 = create_result_node(kungfu.Result[list, TypeError])

    assert result_node1.__from_node__ is str
    assert result_node1.__error__ is RuntimeError

    assert result_node2.__from_node__ is list
    assert result_node2.__error__ is TypeError


def test_create_result_node_no_type_args():
    with pytest.raises(NodeBuildError) as exc_info:
        create_result_node(kungfu.Result)  # type: ignore

    assert "Result must have specified type arguments" in str(exc_info.value)


def test_create_result_node_caching():
    result_node1 = create_result_node(kungfu.Result[int, ValueError])
    result_node2 = create_result_node(kungfu.Result[int, ValueError])
    assert result_node1 is result_node2


def test_create_result_node_custom_error():
    class CustomError(Exception):
        pass

    result_node = create_result_node(kungfu.Result[str, CustomError])

    assert result_node.__from_node__ is str
    assert result_node.__error__ is CustomError
    assert "CustomError" in result_node.__name__
