"""Regression tests for create_node_from_function, union fallbacks, LayerAgent error
propagation, graph-build performance, signatures, scalar naming and polymorphic overrides."""

import functools
import time

import kungfu
import pytest

from nodnod import (
    EventLoopAgent,
    Node,
    NodeError,
    Scope,
    create_node_from_function,
    scalar_node,
)
from nodnod.agent.layer.agent import LayerAgent
from nodnod.error import NodeBuildError
from nodnod.interface.compose_one import compose_one
from nodnod.interface.polymorphic import case, polymorphic


@pytest.mark.asyncio
async def test_compose_one_works_for_function_without_externals():
    """A zero-arg function node must compose via compose_one without an injected Externals
    (regression: Externals was always a required injection)."""
    node = create_node_from_function(lambda: 5)
    assert await compose_one(node) == 5


def test_non_composable_dependency_override_raises():
    with pytest.raises(NodeBuildError, match="must be a `Node`"):
        create_node_from_function(lambda d: d, dependencies={"d": 42})


def test_overriding_composable_dependency_removes_orphan():
    """Overriding a Composable-annotated parameter must remove the node node.py synthesized for
    it, instead of leaving it as an orphan dependency."""
    from nodnod.utils.create_node import create_node_from_composable

    class OldComposable:
        @classmethod
        def __compose__(cls, n: int) -> int:
            return n

    @scalar_node
    class NewDep(Node[int]):
        @classmethod
        def __compose__(cls) -> int:
            return 99

    def func(d: OldComposable) -> int:
        return d

    node = create_node_from_function(func, dependencies={"d": NewDep})

    assert NewDep in node.__dependencies__
    assert create_node_from_composable(OldComposable) not in node.__dependencies__


@pytest.mark.asyncio
async def test_union_falls_back_to_injected_value():
    """`A | int` must fall back to the injected int when A fails (regression: the raw injectable
    branch was inert)."""

    @scalar_node
    class FailA(Node[int]):
        @classmethod
        def __compose__(cls) -> int:
            raise NodeError("A fails")

    @scalar_node
    class Consumer(Node[str]):
        @classmethod
        def __compose__(cls, value: FailA | int) -> str:
            return f"got {value}"

    async with Scope(detail="test") as scope:
        scope.inject(int, 99)
        await EventLoopAgent.build({Consumer}).run(scope, {})
        assert "99" in scope[Consumer].value


@pytest.mark.asyncio
async def test_union_falls_through_absent_middle_injectable():
    """An injectable candidate that is NOT last must fail softly when absent so the union falls
    through to later candidates, rather than raising and aborting the whole union."""

    @scalar_node
    class FailA(Node[int]):
        @classmethod
        def __compose__(cls) -> int:
            raise NodeError("A fails")

    @scalar_node
    class Consumer(Node[str]):
        @classmethod
        def __compose__(cls, value: FailA | int | None) -> str:
            return f"got {value}"

    async with Scope(detail="test") as scope:
        # int is NOT injected: must fall through to None instead of raising "couldn't inject int".
        await EventLoopAgent.build({Consumer}).run(scope, {})
        assert scope[Consumer].value == "got None"


@pytest.mark.asyncio
async def test_layer_agent_single_step_propagates_failure():
    @scalar_node
    class Boom(Node[int]):
        @classmethod
        def __compose__(cls) -> int:
            raise NodeError("boom")

    with pytest.raises(NodeError, match="boom"):
        async with Scope(detail="test") as scope:
            await LayerAgent.build({Boom}).run(scope, {})


@pytest.mark.asyncio
async def test_layer_agent_parallel_step_propagates_failure():
    @scalar_node
    class BoomA(Node[int]):
        @classmethod
        def __compose__(cls) -> int:
            raise NodeError("a")

    @scalar_node
    class BoomB(Node[int]):
        @classmethod
        def __compose__(cls) -> int:
            raise NodeError("b")

    with pytest.raises(NodeError):
        async with Scope(detail="test") as scope:
            await LayerAgent.build({BoomA, BoomB}).run(scope, {})


@pytest.mark.asyncio
async def test_layer_agent_parallel_step_reraises_base_exception():
    class Boom(BaseException):
        pass

    @scalar_node
    class A(Node[int]):
        @classmethod
        def __compose__(cls) -> int:
            raise Boom("x")

    @scalar_node
    class B(Node[int]):
        @classmethod
        def __compose__(cls) -> int:
            return 1

    with pytest.raises(Boom):
        async with Scope(detail="test") as scope:
            await LayerAgent.build({A, B}).run(scope, {})


def test_diamond_graph_builds_in_non_exponential_time():
    """A wide shared-subtree (diamond) graph must build in roughly linear time: validation is
    memoized rather than re-run per path (regression: exponential blowup / DoS)."""
    namespace = {"Node": Node}

    def make(name: str, deps: list[type[Node]]) -> type[Node]:
        for i, dep in enumerate(deps):
            namespace[f"_D_{name}_{i}"] = dep
        params = ", ".join(f"d{i}: _D_{name}_{i}" for i in range(len(deps)))
        src = (
            f"class {name}(Node):\n"
            f"    @classmethod\n"
            f"    def __compose__(cls{', ' + params if params else ''}) -> int:\n"
            f"        return 0\n"
        )
        exec(src, namespace)  # noqa: S102 - controlled source built from a fixed template
        return namespace[name]

    start = time.monotonic()
    prev = [make("Lvl0A", []), make("Lvl0B", [])]
    for level in range(1, 20):
        a = make(f"Lvl{level}A", prev)
        b = make(f"Lvl{level}B", prev)
        prev = [a, b]
    elapsed = time.monotonic() - start

    assert elapsed < 1.0


@pytest.mark.asyncio
async def test_positional_only_param_with_default_is_passed_positionally():
    @scalar_node
    class Dep(Node[int]):
        @classmethod
        def __compose__(cls) -> int:
            return 5

    @scalar_node
    class Consumer(Node[int]):
        @classmethod
        def __compose__(cls, dep: Dep = None, /) -> int:
            return dep

    async with Scope(detail="test") as scope:
        await EventLoopAgent.build({Consumer}).run(scope, {})
        assert scope[Consumer].value == 5


def test_scalar_node_handles_callable_without_name():
    def base() -> int:
        return 5

    node = scalar_node(functools.partial(base))
    assert issubclass(node, Node)


def test_polymorphic_case_override_deduplicates():
    @scalar_node
    class A(Node[int]):
        @classmethod
        def __compose__(cls) -> int:
            return 1

    class BasePoly:
        @case
        def from_a(cls, a: A) -> int:
            return a

    @polymorphic[int]
    class Sub(BasePoly):
        @case
        def from_a(cls, a: A) -> int:
            return a + 100

    assert len(Sub.__either__) == 1
