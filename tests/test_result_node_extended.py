import kungfu
import pytest

from nodnod import EventLoopAgent, Scope, scalar_node
from nodnod.interface.create_result_node import create_result_node


class TestResultNodeExtended:
    def test_create_scalar_node_from_function(self):
        def my_func() -> int:
            ...

        scalar_node_my_func = scalar_node(my_func)

        assert scalar_node_my_func.is_scalar is True  # type: ignore
        assert scalar_node_my_func.__compose__ == my_func  # type: ignore

    def test_scalar_node_error_on_non_function_or_class(self):
        class Dummy:
            ...

        with pytest.raises(TypeError, match="^scalar_node must be kind of class or function, got `.*`"):
            scalar_node(Dummy())

    @pytest.mark.asyncio
    async def test_result_node_with_base_exception(self):
        @scalar_node
        class FailingNode:
            @classmethod
            def __compose__(cls) -> int:
                raise BaseException("System exit error")

        result_type = kungfu.Result[FailingNode, BaseException]
        result_node_class = create_result_node(result_type)

        agent = EventLoopAgent.build({result_node_class})
        scope = Scope(detail="test")

        async with scope:
            await agent.run(local_scope=scope, mapped_scopes={})
            result = scope.retrieve(result_node_class)
            assert kungfu.is_some(result)

            result_value = result.unwrap().value
            assert kungfu.is_err(result_value)
            assert isinstance(result_value.error, BaseException)

    @pytest.mark.asyncio
    async def test_result_node_success_case(self):
        @scalar_node
        class SuccessNode:
            @classmethod
            def __compose__(cls) -> int:
                return 123

        result_type = kungfu.Result[SuccessNode, Exception]
        result_node_class = create_result_node(result_type)

        agent = EventLoopAgent.build({result_node_class})
        scope = Scope(detail="test")

        async with scope:
            await agent.run(local_scope=scope, mapped_scopes={})
            result = scope.retrieve(result_node_class)
            assert kungfu.is_some(result)

            result_value = result.unwrap().value
            assert kungfu.is_ok(result_value)
            assert result_value.unwrap() == 123
