import typing

import pytest

from nodnod import Scope, Node
from nodnod.interface.node_constructor import NodeConstructor, initialize_node_constructor
from nodnod.agent.event_loop.agent import EventLoopAgent
from nodnod.value import Value


class TestInitializeNodeConstructor:
    def test_initialize_node_constructor_basic(self):
        def compose(context: dict[str, typing.Any]) -> int:
            return context.get("x", 0) * 2

        names_by_type = {int: "x"}
        values = {Value(int, 21)}

        result = initialize_node_constructor(compose, names_by_type, values)
        assert result == 42

    def test_initialize_node_constructor_filters_unknown_types(self):
        def compose(context: dict[str, typing.Any]) -> int:
            return context.get("x", 100)

        names_by_type = {int: "x"}
        values = {Value(str, "ignored"), Value(int, 5)}

        result = initialize_node_constructor(compose, names_by_type, values)
        assert result == 5


class TestNodeConstructorBasic:
    def test_node_constructor_sets_initialize(self):
        class MyConstructor(NodeConstructor):
            def __compose__(self) -> int:
                ...

        assert MyConstructor.__initialize__ is not None

    def test_node_constructor_initialize_false_inherits_from_node(self):
        class Constructor(NodeConstructor, initialize=False):
            pass

        assert issubclass(Constructor, NodeConstructor)


class TestNodeConstructorExecution:
    @pytest.mark.asyncio
    async def test_constructor_compose_via_agent(self):
        class Counter(NodeConstructor):
            def __compose__(self) -> int:
                return 100

        agent = EventLoopAgent.build({Counter})

        async with Scope(detail="test") as scope:
            await agent.run(scope, mapped_scopes={})
            result = scope[Counter].value

        assert result == 100

    @pytest.mark.asyncio
    async def test_constructor_with_init_args(self):
        class Multiplier(NodeConstructor):
            def __init__(self, factor: int):
                self.factor = factor

            def __compose__(self) -> int:
                return self.factor * 10

        node = Multiplier[5]
        agent = EventLoopAgent.build({node})

        async with Scope(detail="test") as scope:
            await agent.run(scope, mapped_scopes={})
            result = scope[node].value

        assert result == 50


class TestNodeConstructorClassGetitem:
    def test_class_getitem_single_arg(self):
        class Parameterized(NodeConstructor):
            value: int

            def __init__(self, value: int):
                ...

            def __compose__(self) -> int:
                ...

        node = Parameterized[5]

        assert node.__name__ == "Parameterized[5]"
        assert node.__type__ is node

    def test_class_getitem_multiple_args(self):
        class MultiParam(NodeConstructor):
            a: int
            b: str

            def __init__(self, a: int, b: str):
                ...

            def __compose__(self) -> str:
                ...

        node = MultiParam[10, "hello"]

        assert node.__name__ == "MultiParam[10, hello]"
        assert node.__initialize__ is not None

    @pytest.mark.asyncio
    async def test_class_getitem_execution(self):
        class DoubleValue(NodeConstructor):
            def __init__(self, x: int):
                self.x = x

            def __compose__(self) -> int:
                return self.x * 2

        node = DoubleValue[21]
        agent = EventLoopAgent.build({node})

        async with Scope(detail="test") as scope:
            await agent.run(scope, mapped_scopes={})
            result = scope[node].value

        assert result == 42


class TestNodeConstructorIntegration:
    @pytest.mark.asyncio
    async def test_parameterized_constructor_full_flow(self):
        class Greeter(NodeConstructor):
            def __init__(self, name: str):
                self.name = name

            def __compose__(self) -> str:
                return f"Hello, {self.name}!"

        node = Greeter["World"]
        agent = EventLoopAgent.build({node})

        async with Scope(detail="test") as scope:
            await agent.run(scope, mapped_scopes={})
            result = scope[node].value

        assert result == "Hello, World!"

    @pytest.mark.asyncio
    async def test_parameterized_with_multiple_args(self):
        class MyNode(Node, abstract=True):
            ...

        class Calculator(NodeConstructor):
            def __init__(self, a: int, b: int, op: str):
                self.__map__ = {object: MyNode}
                self.a = a
                self.b = b
                self.op = op

            def __compose__(self) -> int:
                return self.a + self.b if self.op == "+" else self.a - self.b

        node = Calculator[10, 5, "+"]
        agent = EventLoopAgent.build({node})

        async with Scope(detail="test") as scope:
            await agent.run(scope, mapped_scopes={})
            result = scope[node].value

        assert result == 15
