import fntypes
import pytest

from nodnod import EventLoopAgent, Scope, scalar_node
from nodnod.interface.create_result_node import create_result_node


class TestResultNodeExtended:
    @pytest.mark.asyncio
    async def test_result_node_with_base_exception(self):
        @scalar_node
        class FailingNode:
            @classmethod
            def __compose__(cls) -> int:
                raise BaseException("System exit error")

        result_type = fntypes.Result[FailingNode, BaseException]
        result_node_class = create_result_node(result_type)

        agent = EventLoopAgent.build({result_node_class})
        scope = Scope(detail="test")

        async with scope:
            await agent.run(local_scope=scope, mapped_scopes={})
            result = scope.retrieve(result_node_class)
            assert fntypes.is_some(result)

            result_value = result.unwrap().value
            assert fntypes.is_err(result_value)
            assert isinstance(result_value.error, BaseException)

    @pytest.mark.asyncio
    async def test_result_node_success_case(self):
        @scalar_node
        class SuccessNode:
            @classmethod
            def __compose__(cls) -> int:
                return 123

        result_type = fntypes.Result[SuccessNode, Exception]
        result_node_class = create_result_node(result_type)

        agent = EventLoopAgent.build({result_node_class})
        scope = Scope(detail="test")

        async with scope:
            await agent.run(local_scope=scope, mapped_scopes={})
            result = scope.retrieve(result_node_class)
            assert fntypes.is_some(result)

            result_value = result.unwrap().value
            assert fntypes.is_ok(result_value)
            assert result_value.unwrap() == 123
