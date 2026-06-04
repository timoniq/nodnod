import typing

import pytest

from nodnod import Node
from nodnod.node import FORWARD_REF_REQUESTS, INITIALIZED_FORWARD_REFS, Injection


def test_node_with_forward_reference():
    FORWARD_REF_REQUESTS.clear()
    INITIALIZED_FORWARD_REFS.clear()

    class NodeWithForwardRef(Node):
        @classmethod
        def __compose__(cls, dep: "ForwardRefNode") -> None: ...

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
        def __compose__(cls, value: IntAlias) -> None: ...

    assert int in NodeWithTypeAlias.__injections__


def test_node_with_type_parameter():
    T = typing.TypeVar("T")

    class GenericNode(Node):
        __type_params__ = (T,)

        @classmethod
        def __compose__(cls, arg_type: type[T]) -> None: ...

    assert len(GenericNode.__dependencies__) == 1


def test_node_with_type_parameter_invalid():
    with pytest.raises(Exception):

        class InvalidTypeNode(Node):
            @classmethod
            def __compose__(cls, arg_type: type) -> None: ...


def test_node_with_type_parameter_non_typevar():
    with pytest.raises(NotImplementedError):

        class NonTypeVarNode(Node):
            @classmethod
            def __compose__(cls, arg_type: type[int]) -> None: ...


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

    def compose_func(custom_dep: str, regular_dep: int) -> None: ...

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
        def __compose__(cls, injected: Injection[str]) -> None: ...

    assert str in NodeWithInjection.__injections__


def test_injection_annotation_processed():
    class NodeWithMultipleInjections(Node):
        @classmethod
        def __compose__(cls, injected1: Injection[str], injected2: Injection[int]) -> None: ...

    injections = NodeWithMultipleInjections.__injections__ or set()
    assert str in injections
    assert int in injections


def test_forward_ref_resolution_with_existing_ref():
    FORWARD_REF_REQUESTS.clear()
    INITIALIZED_FORWARD_REFS.clear()

    class ExistingNode(Node):
        @classmethod
        def __compose__(cls) -> None: ...

    INITIALIZED_FORWARD_REFS["ExistingNode"] = ExistingNode

    class NodeUsingExistingRef(Node):
        @classmethod
        def __compose__(cls, dep: "ExistingNode") -> None: ...

    assert ExistingNode in NodeUsingExistingRef.__dependencies__


def test_node_repr():
    class TestReprNode(Node):
        @classmethod
        def __compose__(cls) -> None: ...

    instance = TestReprNode()
    assert repr(instance) == "<node `TestReprNode`>"


def test_node_type_self_assignment():
    class SelfTypeNode(Node):
        @classmethod
        def __compose__(cls) -> None: ...

    assert SelfTypeNode.__type__ is SelfTypeNode


def test_node_with_type_var_tuple():
    Ts = typing.TypeVarTuple("Ts")

    class GenericNodeWithTuple(Node):
        __type_params__ = (Ts,)

        @classmethod
        def __compose__(cls, args: tuple[typing.Unpack[Ts]]) -> None: ...

    assert len(GenericNodeWithTuple.__dependencies__) == 1


def test_node_with_tuple_invalid_no_args():
    with pytest.raises(Exception):

        class InvalidTupleNode(Node):
            @classmethod
            def __compose__(cls, arg_tuple: tuple) -> None: ...


def test_node_with_tuple_invalid_non_unpack():
    with pytest.raises(NotImplementedError):

        class NonUnpackTupleNode(Node):
            @classmethod
            def __compose__(cls, arg_tuple: tuple[int, str]) -> None: ...


def test_node_with_tuple_invalid_unpack_non_typevartuple():
    with pytest.raises(NotImplementedError):

        class UnpackNonTVTNode(Node):
            @classmethod
            def __compose__(cls, arg_tuple: tuple[typing.Unpack[tuple[int, str]]]) -> None: ...


def test_node_with_type_var_tuple_mixed_params():
    T = typing.TypeVar("T")
    Ts = typing.TypeVarTuple("Ts")
    U = typing.TypeVar("U")

    class MixedGenericNode(Node):
        __type_params__ = (T, Ts, U)

        @classmethod
        def __compose__(
            cls,
            first_type: type[T],
            middle_types: tuple[typing.Unpack[Ts]],
            last_type: type[U],
        ) -> None: ...

    assert len(MixedGenericNode.__dependencies__) == 3
