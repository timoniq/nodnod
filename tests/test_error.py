import pytest

from nodnod.error import NodeBuildError, NodeError, repr_node_error


class TestNodeError:
    def test_node_error_creation(self):
        error = NodeError("Test error message")
        assert "Test error message" in str(error)

    def test_node_error_with_from_error(self):
        child_error = NodeError("Child error")
        parent_error = NodeError("Parent error", from_error=child_error)

        assert parent_error.from_error is child_error
        assert "Parent error" in str(parent_error)
        assert "Child error" in str(parent_error)

    def test_node_error_with_from_many(self):
        error1 = NodeError("Error 1")
        error2 = NodeError("Error 2")
        parent_error = NodeError("Multiple errors", from_many=[error1, error2])

        assert parent_error.from_many == [error1, error2]
        assert "Multiple errors" in str(parent_error)
        assert "Error 1" in str(parent_error)
        assert "Error 2" in str(parent_error)

    def test_node_error_from_error_and_from_many_conflict(self):
        child_error = NodeError("Child error")
        error_list = [NodeError("Error 1")]

        with pytest.raises(RuntimeError):
            NodeError("Conflict", from_error=child_error, from_many=error_list)

    def test_repr_node_error_simple(self):
        error = NodeError("Simple error")
        repr_str = repr_node_error(error)
        assert "Simple error" in repr_str

    def test_repr_node_error_nested(self):
        child = NodeError("Child error")
        parent = NodeError("Parent error", from_error=child)
        repr_str = repr_node_error(parent)

        assert "Parent error" in repr_str
        assert "Child error" in repr_str
        assert "←" in repr_str

    def test_repr_node_error_multiple(self):
        error1 = NodeError("Error 1")
        error2 = NodeError("Error 2")
        parent = NodeError("Multiple errors", from_many=[error1, error2])
        repr_str = repr_node_error(parent)

        assert "Multiple errors" in repr_str
        assert "Error 1" in repr_str
        assert "Error 2" in repr_str
        assert "*" in repr_str

    def test_node_build_error(self):
        error = NodeBuildError("Build failed")
        assert "Build failed" in str(error)
