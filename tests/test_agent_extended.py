import fntypes
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

        # Create agent with duplicated nodes to hit the continue path
        agent = EventLoopAgent([TestNode, TestNode], final_nodes={TestNode})
        scope = Scope(detail="test")

        async with scope:
            await agent.run(local_scope=scope, mapped_scopes={})
            result = scope.retrieve(TestNode)
            assert fntypes.is_some(result)
            assert result.unwrap().value == 42
