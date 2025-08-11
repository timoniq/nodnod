from nodnod.agent.base import Agent
from nodnod.node import Node, Queue
from nodnod.scope import Scope
from nodnod.interface.either import Either
from nodnod.agent.event_loop.coroutine import compose_coroutine, dependency_sequential_either_coroutine, dependency_concurrent_either_corountine
from nodnod.builder.build_queue import traverse_all
import asyncio
import typing
import fntypes

class EventLoopAgent(Agent):
    def __init__(
        self, 
        traversed_nodes: "Queue",
        final_nodes: typing.Iterable[type[Node]] | None = None,
    ) -> None:
        self.traversed_nodes = traversed_nodes
        self.final_nodes = final_nodes or traversed_nodes

    @classmethod
    def build(cls, nodes: set[type[Node]]) -> typing.Self:
        return cls(traversed_nodes=traverse_all(nodes), final_nodes=nodes)
    
    def push_futures(
        self, 
        local_scope: Scope, 
        mapped_scopes: dict[type[Node], Scope], 
        futures: dict[type[Node], asyncio.Future],
    ) -> None:
        
        for node in self.traversed_nodes:

            if node in futures:
                continue

            if issubclass(node, Either):

                if node.is_concurrent:
                
                    dependencies = [
                        futures[dependency] for dependency in node.__dependencies__
                    ]

                    collect_either = asyncio.Task(
                        dependency_concurrent_either_corountine(
                            dependencies,
                        )
                    )
                
                else:
                    
                    first_dependency_node = node.__either__[0]
                    first_dependency_future = futures[first_dependency_node]

                    other_dependencies = node.__either__[1:]

                    collect_either = asyncio.Task(
                        dependency_sequential_either_coroutine(
                            (first_dependency_node, first_dependency_future),
                            other_dependencies,
                            futures,
                            pusher=lambda _futures, _node: (
                                self.__class__(getattr(_node, "__traverse__"))
                                .push_futures(
                                    local_scope, 
                                    mapped_scopes, 
                                    _futures,
                                )
                            ),
                            mapped_scopes=mapped_scopes,
                            local_scope=local_scope,
                        )
                    )

                task = asyncio.Task(
                    compose_coroutine(
                        node,
                        mapped_scopes.get(node, local_scope),
                        local_scope,
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
                        local_scope,
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
        # Push all network into loop
        for future in futures.values():
            asyncio.ensure_future(future)
        
        final_futures = {futures[node] for node in self.final_nodes}
        
        results = await asyncio.gather(*final_futures)
        for result in results:
            if fntypes.is_err(result):
                raise result.error
