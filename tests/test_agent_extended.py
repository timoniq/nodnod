import kungfu
import pytest

from nodnod import EventLoopAgent, Scope, scalar_node


class TestEventLoopAgentExtended:
    @pytest.mark.asyncio
    async def test_agent_with_duplicate_nodes_in_queue(self):
        @scalar_node
        class TestNode:
            @classmethod
            def __compose__(cls) -> int:
                return 42

        agent = EventLoopAgent([TestNode, TestNode], final_nodes={TestNode})
        scope = Scope(detail="test")

        async with scope:
            await agent.run(local_scope=scope, mapped_scopes={})
            result = scope.retrieve(TestNode)
            assert kungfu.is_some(result)
            assert result.unwrap().value == 42
