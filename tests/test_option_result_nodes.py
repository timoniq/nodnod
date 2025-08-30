import fntypes
import pytest

from nodnod import EventLoopAgent, Node, NodeError, Scope, scalar_node
from nodnod.interface.create_result_node import create_result_node
from nodnod.interface.option_node import create_option_node


class TestOptionNodes:
    @pytest.mark.asyncio
    async def test_option_node_with_some_value(self):
        @scalar_node
        class SuccessNode:
            @classmethod
            def __compose__(cls) -> int:
                return 42

        @scalar_node
        class ConsumerNode:
            @classmethod
            def __compose__(cls, opt: fntypes.Option[SuccessNode]) -> str:
                assert fntypes.is_some(opt)
                return f"Got value: {opt.unwrap()}"

        agent = EventLoopAgent.build({ConsumerNode})
        scope = Scope(detail="test")

        async with scope:
            await agent.run(local_scope=scope, mapped_scopes={})
            result = scope.retrieve(ConsumerNode)
            assert fntypes.is_some(result)
            assert result.unwrap().value == "Got value: 42"

    @pytest.mark.asyncio
    async def test_option_node_with_failing_dependency(self):
        @scalar_node
        class FailingNode:
            @classmethod
            def __compose__(cls) -> int:
                raise NodeError("This fails")

        @scalar_node
        class ConsumerNode:
            @classmethod
            def __compose__(cls, opt: fntypes.Option[FailingNode]) -> str:
                assert fntypes.is_nothing(opt)
                return "No value"

        agent = EventLoopAgent.build({ConsumerNode})
        scope = Scope(detail="test")

        async with scope:
            await agent.run(local_scope=scope, mapped_scopes={})
            result = scope.retrieve(ConsumerNode)
            assert fntypes.is_some(result)
            assert result.unwrap().value == "No value"


class TestResultNodes:
    @pytest.mark.asyncio
    async def test_result_node_with_success(self):
        @scalar_node
        class SuccessNode:
            @classmethod
            def __compose__(cls) -> int:
                return 123

        @scalar_node
        class ConsumerNode:
            @classmethod
            def __compose__(cls, res: fntypes.Result[SuccessNode, Exception]) -> str:
                assert fntypes.is_ok(res)
                return f"Success: {res.unwrap()}"

        agent = EventLoopAgent.build({ConsumerNode})
        scope = Scope(detail="test")

        async with scope:
            await agent.run(local_scope=scope, mapped_scopes={})
            result = scope.retrieve(ConsumerNode)
            assert fntypes.is_some(result)
            assert result.unwrap().value == "Success: 123"

    @pytest.mark.asyncio
    async def test_result_node_with_error(self):
        @scalar_node
        class FailingNode:
            @classmethod
            def __compose__(cls) -> int:
                raise ValueError("Test error")

        @scalar_node
        class ConsumerNode:
            @classmethod
            def __compose__(cls, res: fntypes.Result[FailingNode, Exception]) -> str:
                assert fntypes.is_err(res)
                return f"Error: {type(res.error).__name__}"

        agent = EventLoopAgent.build({ConsumerNode})
        scope = Scope(detail="test")

        async with scope:
            await agent.run(local_scope=scope, mapped_scopes={})
            result = scope.retrieve(ConsumerNode)
            assert fntypes.is_some(result)
            assert "Error:" in result.unwrap().value


class TestNodeCreation:
    def test_create_option_node(self):
        class TestNode(Node, abstract=True):
            __dependencies__ = set()
            __injections__ = set()

        TestNode.__type__ = TestNode

        option_type = fntypes.Option[TestNode]
        option_node = create_option_node(option_type)

        assert issubclass(option_node, Node)
        assert option_node.__type__ is option_type

    def test_create_result_node(self):
        class TestNode(Node, abstract=True):
            __dependencies__ = set()
            __injections__ = set()

        TestNode.__type__ = TestNode

        result_type = fntypes.Result[TestNode, Exception]
        result_node = create_result_node(result_type)

        assert issubclass(result_node, Node)
        assert result_node.__type__ is result_type
        assert result_node.__error__ is Exception  # type: ignore
