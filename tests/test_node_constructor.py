import typing

import pytest

from nodnod import Scope
from nodnod.interface.node_constructor import NodeConstructor, _Constructor
from nodnod.agent.event_loop.agent import EventLoopAgent


class TestNodeConstructorBasic:
    def test_node_constructor_creates_constructor_class(self):
        class MyConstructor(NodeConstructor):
            @classmethod
            def __construct__(cls) -> int:
                ...

        assert MyConstructor.__constructor__ is not None
        assert issubclass(MyConstructor.__constructor__, _Constructor)
        assert MyConstructor.__constructor__ in MyConstructor.__dependencies__

    def test_node_constructor_abstract_does_not_create_constructor(self):
        class AbstractConstructor(NodeConstructor, abstract=True):
            pass

        assert AbstractConstructor.__constructor__ is None

    def test_constructor_not_implemented_raises(self):
        with pytest.raises(NotImplementedError, match="`__construct__` method must be implemented"):
            NodeConstructor.__construct__()

    def test_init_subclass_sets_injections(self):
        class SimpleConstructor(NodeConstructor):
            @classmethod
            def __construct__(cls) -> int:
                ...

        assert SimpleConstructor.__constructor__ in SimpleConstructor.__injections__


class TestNodeConstructorExecution:
    @pytest.mark.asyncio
    async def test_constructor_compose_via_agent(self):
        class Counter(NodeConstructor):
            @classmethod
            def __construct__(cls) -> int:
                return 100

        constructor = Counter.__constructor__
        agent = EventLoopAgent.build({constructor})

        async with Scope(detail="test") as scope:
            await agent.run(scope, mapped_scopes={})
            result = scope[constructor].value

        assert result == 100


class TestNodeConstructorClassGetitem:
    def test_class_getitem_single_arg(self):
        class Parameterized(NodeConstructor):
            @classmethod
            def __construct__(cls, value: int) -> int:
                ...

        node = Parameterized[5]

        assert node.__name__ == "Parameterized[5]"
        assert node.__constructor__ is not None
        assert node.__type__ is node

    def test_class_getitem_multiple_args(self):
        class MultiParam(NodeConstructor):
            @classmethod
            def __construct__(cls, a: int, b: str) -> str:
                ...

        node = MultiParam[10, "hello"]

        assert node.__name__ == "MultiParam[10, hello]"
        assert node.__constructor__ is not None

    @pytest.mark.asyncio
    async def test_class_getitem_execution(self):
        class DoubleValue(NodeConstructor):
            @classmethod
            def __construct__(cls, x: int) -> int:
                return x * 2

        node = DoubleValue[21]
        constructor = node.__constructor__
        agent = EventLoopAgent.build({constructor})

        async with Scope(detail="test") as scope:
            await agent.run(scope, mapped_scopes={})
            result = scope[constructor].value

        assert result == 42

    def test_class_getitem_sets_dependencies_and_injections(self):
        class WithArgs(NodeConstructor):
            @classmethod
            def __construct__(cls, x: int) -> int:
                ...

        node = WithArgs[5]

        assert node.__constructor__ in node.__dependencies__
        assert node.__constructor__ in node.__injections__

    def test_class_getitem_creates_new_constructor(self):
        class Parent(NodeConstructor):
            @classmethod
            def __construct__(cls) -> int:
                ...

        parent_constructor = Parent.__constructor__
        node = Parent[5]
        node_constructor = node.__constructor__

        assert node_constructor is not parent_constructor
        assert node_constructor in node.__dependencies__
        assert "Parent[5]" in node_constructor.__name__


class TestConstructorClass:
    def test_constructor_has_self_type(self):
        assert _Constructor.__type__ == typing.Self

    def test_constructor_compose_calls_construct(self):
        class TestNode(NodeConstructor):
            @classmethod
            def __construct__(cls) -> str:
                return "constructed"

        constructor = TestNode.__constructor__
        assert constructor is not None

        result = constructor.__compose__()
        assert result == "constructed"


class TestNodeConstructorIntegration:
    @pytest.mark.asyncio
    async def test_parameterized_constructor_full_flow(self):
        class Greeter(NodeConstructor):
            @classmethod
            def __construct__(cls, name: str) -> str:
                return f"Hello, {name}!"

        node = Greeter["World"]
        constructor = node.__constructor__
        agent = EventLoopAgent.build({constructor})

        async with Scope(detail="test") as scope:
            await agent.run(scope, mapped_scopes={})
            result = scope[constructor].value

        assert result == "Hello, World!"

    @pytest.mark.asyncio
    async def test_parameterized_with_multiple_args(self):
        class Calculator(NodeConstructor):
            @classmethod
            def __construct__(cls, a: int, b: int, op: str) -> int:
                return a + b if op == "+" else a - b

        node = Calculator[10, 5, "+"]
        constructor = node.__constructor__
        agent = EventLoopAgent.build({constructor})

        async with Scope(detail="test") as scope:
            await agent.run(scope, mapped_scopes={})
            result = scope[constructor].value

        assert result == 15
