import pytest
from typing_extensions import ForwardRef

from nodnod import Injection, Node, Scope, scalar_node, create_agent_from_node, inject_externals
from nodnod.agent.event_loop.agent import EventLoopAgent
from nodnod.interface.node_from_function import (
    Externals,
    _NameDict,
    create_node_from_function,
)


class TestCreateNodeFromFunction:
    def test_create_node_from_simple_function(self):
        def my_func() -> int: ...

        node = create_node_from_function(my_func)

        assert (
            node.__name__
            == "Node:TestCreateNodeFromFunction.test_create_node_from_simple_function.<locals>.my_func"
        )
        assert issubclass(node, Node)
        assert node.__compose__ is my_func

    def test_create_node_from_function_with_dependencies(self):
        @scalar_node
        class DepNode:
            @classmethod
            def __compose__(cls) -> int: ...

        def my_func(dep: DepNode) -> int: ...

        node = create_node_from_function(my_func)

        assert (
            node.__name__
            == "Node:TestCreateNodeFromFunction.test_create_node_from_function_with_dependencies.<locals>.my_func"
        )
        assert DepNode in node.__dependencies__

    def test_create_node_with_externals(self):
        def func_with_external(name: str, age: int) -> str: ...

        class Age(Node): ...

        node = create_node_from_function(func_with_external, dependencies={"age": Age})

        assert hasattr(node, "__externals__")
        assert "name" in getattr(node, "__externals__")
        assert "age" not in getattr(node, "__externals__")
        assert Externals in node.__injections__

    @pytest.mark.asyncio
    async def test_node_from_function_execution(self):
        def double(x: int) -> int:
            return x * 2

        node = create_node_from_function(double)
        agent = create_agent_from_node(node)

        async with Scope(detail="test") as scope:
            inject_externals(scope, {"x": 21})
            await agent.run(scope, mapped_scopes={})
            result = scope[node].value

        assert result == 42

    def test_node_from_function_initialize_error_on_missing_dependency(self):
        from nodnod.error import NodeError

        def func(x: int) -> int: ...

        node = create_node_from_function(func)

        with pytest.raises(
            NodeError,
            match=r"Name `x` was not found. Inject it through one of `Injection\[T\]` or `Externals`, or, if it is a `Node` dependency, check its type\.$",
        ):
            node.__initialize__(set())

    @pytest.mark.asyncio
    async def test_node_from_function_with_node_dependency(self):
        @scalar_node
        class BaseValue:
            @classmethod
            def __compose__(cls) -> int:
                return 5

        def multiply(base: BaseValue, factor: int) -> int:
            return base * factor

        node = create_node_from_function(multiply)
        agent = create_agent_from_node(node)

        async with Scope(detail="test") as scope:
            inject_externals(scope, {"factor": 3})
            await agent.run(scope, mapped_scopes={})
            result = scope[node].value

        assert result == 15

    def test_create_node_from_function_error_on_non_callable(self):
        class Dummy: ...

        with pytest.raises(TypeError, match="^`func` must be kind of function, got `.*`"):
            create_node_from_function(Dummy())  # type: ignore

    def test_create_node_from_function_with_custom_dependencies_and_injections(self):
        @scalar_node
        class ANode:
            @classmethod
            def __compose__(cls) -> int: ...

        @scalar_node
        class BNode:
            @classmethod
            def __compose__(cls) -> int: ...

        def func(n: ANode, b: Injection[int]) -> None: ...

        node = create_node_from_function(func, dependencies={"n": BNode, "b": BNode})  # type: ignore
        assert int not in node.__injections__
        assert BNode in node.__dependencies__


class TestCreateAgentFromNode:
    def test_create_agent_from_simple_node(self):
        @scalar_node
        class SimpleNode:
            @classmethod
            def __compose__(cls) -> int: ...

        agent = create_agent_from_node(SimpleNode)  # type: ignore

        assert isinstance(agent, EventLoopAgent)


class TestInjectExternals:
    @pytest.mark.asyncio
    async def test_inject_externals_basic(self):
        async with Scope(detail="test") as scope:
            inject_externals(scope, {"a": 1, "b": "hello"})

            externals = scope[Externals].value
            assert externals["a"] == 1
            assert externals["b"] == "hello"


class TestNameDict:
    def test_name_dict_basic_access(self):
        d = _NameDict()
        d["key"] = "value"

        assert d["key"] == "value"

    def test_name_dict_with_forward_ref(self):
        d = _NameDict()
        d["SomeType"] = "val"

        assert d[ForwardRef("SomeType")] == "val"

    def test_name_dict_key_error(self):
        class UnknownType:
            pass

        d = _NameDict()

        with pytest.raises(KeyError):
            _ = d[UnknownType]


class TestExternals:
    def test_externals_is_dict(self):
        ext = Externals({"a": 1, "b": 2})

        assert ext["a"] == 1
        assert ext["b"] == 2
        assert isinstance(ext, dict)


class TestInitializeNodeWithExternals:
    @pytest.mark.asyncio
    async def test_initialize_with_externals(self):
        def greet(name: str, greeting: str) -> str:
            return f"{greeting}, {name}!"

        node = create_node_from_function(greet)
        agent = create_agent_from_node(node)

        async with Scope(detail="test") as scope:
            inject_externals(scope, {"name": "World", "greeting": "Hello"})
            await agent.run(scope, mapped_scopes={})
            result = scope[node].value

        assert result == "Hello, World!"


class TestNodeFromFunctionWithInjection:
    def test_function_with_node_as_dependency(self):
        @scalar_node
        class Config:
            @classmethod
            def __compose__(cls) -> dict: ...

        def process(cfg: Config) -> str: ...

        node = create_node_from_function(process)

        assert Config in node.__dependencies__


class TestNodeFromFunctionForwardRefs:
    def test_forward_refs_with_explicit_refs(self):
        @scalar_node
        class MyDep:
            @classmethod
            def __compose__(cls) -> int: ...

        def func_with_forward_ref(dep: "MyDep") -> int: ...

        node = create_node_from_function(func_with_forward_ref, forward_refs={"MyDep": MyDep})

        assert (
            node.__name__
            == "Node:TestNodeFromFunctionForwardRefs.test_forward_refs_with_explicit_refs.<locals>.func_with_forward_ref"
        )

    @pytest.mark.asyncio
    async def test_forward_ref_as_external(self):
        def func_with_unknown_forward_ref(data: "UnknownType") -> str:  # type: ignore
            return str(data)

        node = create_node_from_function(func_with_unknown_forward_ref)
        agent = create_agent_from_node(node)

        async with Scope(detail="test") as scope:
            inject_externals(scope, {"data": {"key": "value"}})
            await agent.run(scope, mapped_scopes={})
            result = scope[node].value

        assert result == "{'key': 'value'}"


class TestCollectExternalsHook:
    def test_injection_type_is_internal(self):
        from nodnod.node import Injection

        @scalar_node
        class ConfigNode:
            @classmethod
            def __compose__(cls) -> dict: ...

        def func_with_injection(cfg: Injection[ConfigNode], name: str) -> str: ...

        node = create_node_from_function(func_with_injection)

        externals = getattr(node, "__externals__", [])
        assert "name" in externals


class TestNodeFromFunctionErrors:
    def test_forward_ref_becomes_external_dependency(self):
        from nodnod.node import FORWARD_REF_REQUESTS, INITIALIZED_FORWARD_REFS  # type: ignore

        def func_with_node_ref(dep: "NonExistentNodeType") -> int:  # type: ignore
            ...

        original_refs = dict(INITIALIZED_FORWARD_REFS)
        original_reqs = dict(FORWARD_REF_REQUESTS)

        try:
            INITIALIZED_FORWARD_REFS.clear()
            FORWARD_REF_REQUESTS.clear()
            node = create_node_from_function(func_with_node_ref)
            assert node is not None
        finally:
            INITIALIZED_FORWARD_REFS.clear()
            INITIALIZED_FORWARD_REFS.update(original_refs)
            FORWARD_REF_REQUESTS.clear()
            FORWARD_REF_REQUESTS.update(original_reqs)
