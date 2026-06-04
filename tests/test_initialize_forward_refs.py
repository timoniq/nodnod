import pytest

from nodnod import Node
from nodnod.node import (
    FORWARD_REF_REQUESTS,
    INITIALIZED_FORWARD_REFS,
    initialize_forward_refs,
)


class TestInitializeForwardRefs:
    def setup_method(self) -> None:
        FORWARD_REF_REQUESTS.clear()
        INITIALIZED_FORWARD_REFS.clear()

    def test_initialize_forward_refs_with_found_refs(self):
        class DependentNode(Node, abstract=True):
            pass

        FORWARD_REF_REQUESTS["MockNode"].append(DependentNode)

        class MockNode(Node):
            @classmethod
            def __compose__(cls) -> None:
                ...

        initialize_forward_refs({"MockNode": MockNode})

        assert "MockNode" in INITIALIZED_FORWARD_REFS
        assert INITIALIZED_FORWARD_REFS["MockNode"] is MockNode
        assert "MockNode" not in FORWARD_REF_REQUESTS

    def test_initialize_forward_refs_calls_init_subclass_on_dependencies(self):
        init_subclass_called = []

        class TrackingNode(Node, abstract=True):
            @classmethod
            def __init_subclass__(cls, **kwargs):
                init_subclass_called.append(cls)
                super().__init_subclass__(**kwargs)

        class DependentTrackingNode(TrackingNode, abstract=True):
            @classmethod
            def __compose__(cls, dep: "TargetNode") -> None:
                ...

        FORWARD_REF_REQUESTS["TargetNode"].append(DependentTrackingNode)
        init_subclass_called.clear()

        class TargetNode(Node):
            @classmethod
            def __compose__(cls) -> None:
                ...

        initialize_forward_refs({"TargetNode": TargetNode})

        assert DependentTrackingNode in init_subclass_called

    def test_initialize_forward_refs_external_dependency_when_from_function(self):
        from nodnod.interface.node_from_function import ExternalDependency

        class DependentNode(Node, abstract=True):
            pass

        FORWARD_REF_REQUESTS["UnknownType"].append(DependentNode)

        initialize_forward_refs({}, is_from_function=True)

        assert "UnknownType" in INITIALIZED_FORWARD_REFS
        assert isinstance(INITIALIZED_FORWARD_REFS["UnknownType"], ExternalDependency)
        assert str(INITIALIZED_FORWARD_REFS["UnknownType"]) == "UnknownType"
        assert "UnknownType" not in FORWARD_REF_REQUESTS

    def test_initialize_forward_refs_raises_lookup_error_when_not_from_function(self):
        class DependentNode(Node, abstract=True):
            pass

        FORWARD_REF_REQUESTS["MissingType"].append(DependentNode)

        with pytest.raises(LookupError, match="Dependency `MissingType` not found"):
            initialize_forward_refs({})

    def test_initialize_forward_refs_processes_all_requests(self):
        class DependentNode1(Node, abstract=True):
            pass

        class DependentNode2(Node, abstract=True):
            pass

        FORWARD_REF_REQUESTS["TypeA"].append(DependentNode1)
        FORWARD_REF_REQUESTS["TypeB"].append(DependentNode2)

        class TypeA(Node):
            @classmethod
            def __compose__(cls) -> None:
                ...

        class TypeB(Node):
            @classmethod
            def __compose__(cls) -> None:
                ...

        initialize_forward_refs({"TypeA": TypeA, "TypeB": TypeB})

        assert "TypeA" in INITIALIZED_FORWARD_REFS
        assert "TypeB" in INITIALIZED_FORWARD_REFS
        assert INITIALIZED_FORWARD_REFS["TypeA"] is TypeA
        assert INITIALIZED_FORWARD_REFS["TypeB"] is TypeB
        assert len(FORWARD_REF_REQUESTS) == 0

    def test_initialize_forward_refs_with_multiple_dependencies_per_type(self):
        class DependentNode1(Node, abstract=True):
            pass

        class DependentNode2(Node, abstract=True):
            pass

        class SharedType(Node):
            @classmethod
            def __compose__(cls) -> None:
                ...

        FORWARD_REF_REQUESTS["SharedType"].append(DependentNode1)
        FORWARD_REF_REQUESTS["SharedType"].append(DependentNode2)

        initialize_forward_refs({"SharedType": SharedType})

        assert "SharedType" in INITIALIZED_FORWARD_REFS
        assert INITIALIZED_FORWARD_REFS["SharedType"] is SharedType
        assert "SharedType" not in FORWARD_REF_REQUESTS

    def test_initialize_forward_refs_empty_requests(self):
        FORWARD_REF_REQUESTS.clear()

        initialize_forward_refs({})
        initialize_forward_refs({}, is_from_function=True)

        assert len(FORWARD_REF_REQUESTS) == 0

    def test_initialize_forward_refs_mixed_found_and_external(self):
        from nodnod.interface.node_from_function import ExternalDependency

        class DependentNode1(Node, abstract=True):
            pass

        class DependentNode2(Node, abstract=True):
            pass

        class FoundType(Node):
            @classmethod
            def __compose__(cls) -> None:
                ...

        FORWARD_REF_REQUESTS["FoundType"].append(DependentNode1)
        FORWARD_REF_REQUESTS["ExternalType"].append(DependentNode2)

        initialize_forward_refs({"FoundType": FoundType}, is_from_function=True)

        assert INITIALIZED_FORWARD_REFS["FoundType"] is FoundType
        assert isinstance(INITIALIZED_FORWARD_REFS["ExternalType"], ExternalDependency)
        assert str(INITIALIZED_FORWARD_REFS["ExternalType"]) == "ExternalType"
