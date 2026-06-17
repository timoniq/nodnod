"""Regression tests for Node.__init_subclass__ metaprogramming: forward refs, injection
key-by-type, duplicate-type detection, var-args, and forward-ref localns shadowing."""

import pytest

from nodnod import EventLoopAgent, Injection, Node, NodeError, Scope, inject_internals, scalar_node
from nodnod.error import NodeBuildError
from nodnod.node import FORWARD_REF_REQUESTS, INITIALIZED_FORWARD_REFS


def test_self_referential_forward_ref_raises_clear_circular_dependency():
    with pytest.raises(NodeBuildError, match="Circular dependency"):

        class SelfRef(Node):
            @classmethod
            def __compose__(cls, me: "SelfRef") -> int:
                return 1


@pytest.mark.asyncio
async def test_injection_param_is_keyed_by_unwrapped_type():
    """Injection[T] on a compose param must resolve at compose time (regression: the name map
    was keyed by the Injection[T] wrapper, not by T, so the param was dropped)."""

    @scalar_node
    class Service(Node[str]):
        @classmethod
        def __compose__(cls, cfg: Injection[dict]) -> str:
            return cfg["k"]

    async with Scope(detail="test") as scope:
        inject_internals(scope, {dict: {"k": "value"}})
        await EventLoopAgent.build({Service}).run(scope, {})
        assert scope[Service].value == "value"


def test_two_params_of_same_type_raise_at_definition():
    @scalar_node
    class Dep(Node[int]):
        @classmethod
        def __compose__(cls) -> int:
            return 1

    with pytest.raises(NodeBuildError, match="same dependency type"):

        @scalar_node
        class Bad(Node[int]):
            @classmethod
            def __compose__(cls, first: Dep, second: Dep) -> int:
                return first + second


def test_annotated_var_positional_raises():
    with pytest.raises(NodeBuildError, match="cannot be wired"):

        class VarNode(Node):
            @classmethod
            def __compose__(cls, *deps: int) -> int:
                return 0


def test_unannotated_var_args_are_allowed():
    class VarNode(Node):
        @classmethod
        def __compose__(cls, *args, **kwargs) -> int:
            return 0

    assert VarNode.__dependencies__ == set()


def test_class_attribute_does_not_shadow_dependency_forward_ref():
    """A class attribute whose name matches a forward-ref'd dependency type must not shadow the
    real dependency during forward-ref evaluation."""

    @scalar_node
    class ShadowDep(Node[int]):
        @classmethod
        def __compose__(cls) -> int:
            return 7

    @scalar_node
    class Consumer(Node[int]):
        ShadowDep = int  # accidental class attribute named like the dependency type

        @classmethod
        def __compose__(cls, dep: "ShadowDep") -> int:
            return dep

    assert ShadowDep in Consumer.__dependencies__
    assert int not in Consumer.__injections__


def test_nested_composable_class_forward_ref_still_resolves():
    """Dropping plain class attributes from the forward-ref localns must NOT also break a genuine
    nested class referenced by string (it stays in localns via its qualname)."""

    @scalar_node
    class Outer(Node[int]):
        class Inner:
            @classmethod
            def __compose__(cls) -> int:
                return 5

        @classmethod
        def __compose__(cls, x: "Inner") -> int:
            return x

    assert Outer.__dependencies__ is not None
    assert len(Outer.__dependencies__) == 1


class TestForwardRefGlobalState:
    def setup_method(self) -> None:
        FORWARD_REF_REQUESTS.clear()

    def test_function_node_does_not_drain_unrelated_pending_class_node(self):
        """Building an unrelated function node must not consume a class node's pending forward-ref
        request and leave it permanently uninitialized."""
        from nodnod import create_node_from_function

        class Pending(Node):
            @classmethod
            def __compose__(cls, dep: "PendingTargetUnique") -> int:
                return 1

        assert Pending.__dependencies__ is None  # parked, waiting for its forward ref

        # An unrelated function node is built in between.
        create_node_from_function(lambda: 5)

        # The class node's request must survive ...
        assert "PendingTargetUnique" in FORWARD_REF_REQUESTS

        class PendingTargetUnique(Node):
            @classmethod
            def __compose__(cls) -> int:
                return 2

        # ... so defining the target now resolves Pending.
        assert Pending.__dependencies__ is not None
        assert PendingTargetUnique in Pending.__dependencies__

    def test_name_collision_with_pending_request_warns(self):
        class First(Node, abstract=True):
            pass

        class Waiter(Node, abstract=True):
            pass

        INITIALIZED_FORWARD_REFS["CollideName"] = First
        FORWARD_REF_REQUESTS["CollideName"].append(Waiter)

        with pytest.warns(RuntimeWarning, match="ambiguous"):

            class CollideName(Node):
                @classmethod
                def __compose__(cls) -> int:
                    return 1

        INITIALIZED_FORWARD_REFS.pop("CollideName", None)
        FORWARD_REF_REQUESTS.pop("CollideName", None)

    def test_function_forward_ref_colliding_with_pending_class_request_still_builds(self):
        """A function node whose forward ref shares a name with an already-pending class request
        must build (its parameter becomes an external) WITHOUT destroying the class's request."""
        from nodnod import create_node_from_function

        class Repo(Node):
            @classmethod
            def __compose__(cls, conn: "ConnUnique") -> int:
                return 1

        assert Repo.__dependencies__ is None
        assert "ConnUnique" in FORWARD_REF_REQUESTS

        def handler(conn: "ConnUnique") -> int:
            return 1

        node = create_node_from_function(handler)

        # The function builds (its parameter becomes an external) ...
        assert "conn" in getattr(node, "__externals__")
        # ... and the foreign class's pending request must SURVIVE ...
        assert "ConnUnique" in FORWARD_REF_REQUESTS
        assert Repo in FORWARD_REF_REQUESTS["ConnUnique"]

        # ... so defining the real type now resolves the class node. (Defining a real Node under
        # a name the function already marked external is itself an ambiguity, so #5 warns.)
        with pytest.warns(RuntimeWarning, match="ambiguous"):

            class ConnUnique(Node):
                @classmethod
                def __compose__(cls) -> int:
                    return 2

        assert Repo.__dependencies__ is not None
        assert ConnUnique in Repo.__dependencies__
