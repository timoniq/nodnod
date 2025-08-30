import typing

import pytest

from nodnod import Node
from nodnod.node import FORWARD_REF_REQUESTS, INITIALIZED_FORWARD_REFS, Injection


def test_node_with_forward_reference():
    FORWARD_REF_REQUESTS.clear()
    INITIALIZED_FORWARD_REFS.clear()

    class NodeWithForwardRef(Node):
        @classmethod
        def __compose__(cls, dep: "ForwardRefNode") -> None:
            pass  # pragma: no cover

    assert "ForwardRefNode" in FORWARD_REF_REQUESTS
    assert NodeWithForwardRef in FORWARD_REF_REQUESTS["ForwardRefNode"]

    class ForwardRefNode(Node):
        pass

    assert "ForwardRefNode" in INITIALIZED_FORWARD_REFS
    assert INITIALIZED_FORWARD_REFS["ForwardRefNode"] is ForwardRefNode


def test_node_with_type_alias():
    IntAlias = typing.TypeAliasType("IntAlias", int)

    class NodeWithTypeAlias(Node):
        @classmethod
        def __compose__(cls, value: IntAlias) -> None:
            pass  # pragma: no cover

    assert int in NodeWithTypeAlias.__injections__


def test_node_with_type_parameter():
    T = typing.TypeVar("T")

    class GenericNode(Node):
        __type_params__ = (T,)

        @classmethod
        def __compose__(cls, arg_type: type[T]) -> None:
            pass  # pragma: no cover

    assert len(GenericNode.__dependencies__) == 1


def test_node_with_type_parameter_invalid():
    with pytest.raises(Exception):

        class InvalidTypeNode(Node):
            @classmethod
            def __compose__(cls, arg_type: type) -> None:
                pass  # pragma: no cover


def test_node_with_type_parameter_non_typevar():
    with pytest.raises(NotImplementedError):

        class NonTypeVarNode(Node):
            @classmethod
            def __compose__(cls, arg_type: type[int]) -> None:
                pass  # pragma: no cover


def test_injection_hook():
    hook_called = False
    processed_deps = []

    def custom_hook(cls, dep_name, dep_type):
        nonlocal hook_called
        processed_deps.append((cls, dep_name, dep_type))
        if dep_type is str and dep_name == "custom_dep":
            hook_called = True
            return True
        return False

    from nodnod.utils.create_node import create_node

    def compose_func(custom_dep: str, regular_dep: int) -> None:
        pass  # pragma: no cover

    NodeWithCustomInjection = create_node(
        name="NodeWithCustomInjection",
        base_node=Node,
        bases=(),
        namespace={"__compose__": compose_func},
        injection_hooks=(custom_hook,),
    )

    assert hook_called
    assert len(processed_deps) == 2

    injections = NodeWithCustomInjection.__injections__ or set()
    assert str not in injections
    assert int in injections


def test_injection_annotation():
    class NodeWithInjection(Node):
        @classmethod
        def __compose__(cls, injected: Injection[str]) -> None:
            pass  # pragma: no cover

    assert str in NodeWithInjection.__injections__


def test_injection_annotation_processed():
    class NodeWithMultipleInjections(Node):
        @classmethod
        def __compose__(cls, injected1: Injection[str], injected2: Injection[int]) -> None:
            pass  # pragma: no cover

    injections = NodeWithMultipleInjections.__injections__ or set()
    assert str in injections
    assert int in injections


def test_forward_ref_resolution_with_existing_ref():
    FORWARD_REF_REQUESTS.clear()
    INITIALIZED_FORWARD_REFS.clear()

    class ExistingNode(Node):
        @classmethod
        def __compose__(cls) -> None:
            pass  # pragma: no cover

    INITIALIZED_FORWARD_REFS["ExistingNode"] = ExistingNode

    class NodeUsingExistingRef(Node):
        @classmethod
        def __compose__(cls, dep: "ExistingNode") -> None:
            pass  # pragma: no cover

    assert ExistingNode in NodeUsingExistingRef.__dependencies__


def test_node_repr():
    class TestReprNode(Node):
        @classmethod
        def __compose__(cls) -> None:
            pass  # pragma: no cover

    instance = TestReprNode()
    assert repr(instance) == "<node `TestReprNode`>"


def test_node_type_self_assignment():
    class SelfTypeNode(Node):
        @classmethod
        def __compose__(cls) -> None:
            pass  # pragma: no cover

    assert SelfTypeNode.__type__ is SelfTypeNode
