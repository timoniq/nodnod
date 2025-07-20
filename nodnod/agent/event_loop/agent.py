from nodnod.agent.base import Agent
from nodnod.node import Node
from nodnod.scope import Scope
from nodnod.interface.either import Either
from nodnod.agent.event_loop.coroutine import compose_coroutine, dependency_sequential_either_coroutine, dependency_concurrent_either_corountine
from nodnod.builder.build_queue import traverse_all, Queue
import asyncio
import typing

class EventLoopAgent(Agent):
    def __init__(self, traversed_nodes: Queue) -> None:
        self.traversed_nodes = traversed_nodes

    @classmethod
    def build(cls, nodes: set[type[Node]]) -> typing.Self:
        return cls(traversed_nodes=traverse_all(nodes))
    
    def push_futures(
        self, 
        local_scope: Scope, 
        mapped_scopes: dict[type[Node], Scope], 
        futures: dict[type[Node], asyncio.Future],
    ) -> None:
        
        for node in self.traversed_nodes:

            if issubclass(node, Either):

                if node.concurrent:
                
                    dependencies = [
                        futures[dependency] for dependency in node.__dependencies__
                    ]

                    collect_either = asyncio.Task(
                        dependency_concurrent_either_corountine(
                            dependencies,
                        )
                    )
                
                else:
                    
                    first_dependency = futures[node.__either__[0]]

                    other_dependencies = node.__either__[1:]

                    collect_either = asyncio.Task(
                        dependency_sequential_either_coroutine(
                            first_dependency,
                            other_dependencies,
                            futures,
                            pusher=lambda _futures, _node: (
                                self.__class__(_node.__traverse__)
                                .push_futures(
                                    local_scope, 
                                    mapped_scopes, 
                                    _futures,
                                )
                            ),
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
                    futures[dependency] for dependency in node.__dependencies__
                ]
                task = asyncio.Task(
                    compose_coroutine(
                        node, 
                        mapped_scopes.get(node, local_scope), 
                        dependencies,
                    )
                )
            
            futures[node] = task
    
    async def run(
        self, 
        local_scope: Scope, 
        mapped_scopes: dict[type[Node], Scope],
        futures: dict[type[Node], asyncio.Future] | None = None,
    ):
        futures = futures if futures is not None else {}
        self.push_futures(
            local_scope,
            mapped_scopes,
            futures,
        )
        await asyncio.gather(*futures.values())
        
