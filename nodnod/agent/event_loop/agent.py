from typing import Self
from nodnod.agent.base import Agent
from nodnod.node import Node
from nodnod.scope import Scope
from nodnod.interface.either import Either
from nodnod.error import NodeError
from nodnod.agent.event_loop.coroutine import compose_coroutine, dependency_either_coroutine, dependency_concurrent_either_corountine
from nodnod.builder.build_queue import traverse_all, Queue
from nodnod.box import Box
import asyncio


class EventLoopAgent(Agent):
    def __init__(self, traversed_nodes: Queue) -> None:
        self.traversed_nodes = traversed_nodes

    @classmethod
    def build(cls, nodes: set[type[Node]]) -> Self:
        return cls(traversed_nodes=traverse_all(nodes))
    
    async def run(
        self, 
        local_scope: Scope, 
        mapped_scopes: dict[type[Node], Scope]
    ):
        tasks: dict[type[Node], asyncio.Future] = {}

        for node in self.traversed_nodes:

            if issubclass(node, Either):

                if not node.concurrent:
                    raise RuntimeError("Sequential either not yet supported")
                
                dependencies = [
                    tasks[dependency] for dependency in node.__dependencies__
                ]

                collect_either = asyncio.Task(
                    dependency_concurrent_either_corountine(
                        dependencies,
                    )
                )

                task = asyncio.Task(
                    compose_coroutine(
                        node,
                        mapped_scopes.get(node, local_scope),
                        [collect_either],
                    )
                )

            else:

                dependencies = [
                    tasks[dependency] for dependency in node.__dependencies__
                ]
                task = asyncio.Task(
                    compose_coroutine(
                        node, 
                        mapped_scopes.get(node, local_scope), 
                        dependencies,
                    )
                )
            
            tasks[node] = task
        
        await asyncio.gather(*tasks.values())
        
