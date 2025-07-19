from nodnod.builder.steps import Parallel, ComposeOne
from nodnod.agent.base import Agent
from nodnod.node import Node
from nodnod.scope import Scope
import asyncio


class AsyncAgent(Agent):

    async def run(self, local_scope: Scope, node_scopes: dict[type[Node], Scope]):
        from nodnod.composer import compose_node

        for step in self.steps:
            match step:
                case Parallel(nodes=nodes):
                    coros = [
                        compose_node(node, node_scopes.get(node, local_scope))
                        for node in nodes
                    ]
                    await asyncio.gather(*coros)
                case ComposeOne(node=node):
                    await compose_node(node, node_scopes.get(node, local_scope))
