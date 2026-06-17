import asyncio
import typing

import kungfu

from nodnod.agent.base import Agent
from nodnod.agent.event_loop.coroutine import (
    compose_coroutine,
    compose_either_coroutine,
    dependency_concurrent_either_coroutine,
    dependency_sequential_either_coroutine,
    result_node_compose_coroutine,
)
from nodnod.builder.build_queue import build_queue, traverse_all
from nodnod.scope import Scope, validate_local_scope_is_linked_to_node_scopes

if typing.TYPE_CHECKING:
    from nodnod.node import Node, Queue


class EventLoopAgent(Agent):
    def __init__(
        self,
        traversed_nodes: "Queue",
        final_nodes: typing.Iterable[type["Node"]] | None = None,
    ) -> None:
        self.traversed_nodes = traversed_nodes
        self.final_nodes = final_nodes or traversed_nodes

    @classmethod
    def build(cls, nodes: set[type["Node"]]) -> typing.Self:
        return cls(traversed_nodes=traverse_all(nodes), final_nodes=nodes)

    def push_futures(
        self,
        local_scope: Scope,
        mapped_scopes: dict[type["Node"], Scope],
        futures: dict[type["Node"], asyncio.Future],
    ) -> None:
        from nodnod.interface.either import Either
        from nodnod.interface.result_node import ResultNode

        for node in self.traversed_nodes:
            if node in futures:
                continue

            if issubclass(node, Either):
                if node.is_concurrent:

                    dependencies = [
                        futures[dependency] for dependency in node.__dependencies__
                    ]

                    collect_either = asyncio.Task(
                        dependency_concurrent_either_coroutine(
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
                                # Either subclasses (Option/Union/nested either) never get a
                                # `__traverse__`, so fall back to building it on demand instead
                                # of crashing with AttributeError.
                                self.__class__(getattr(_node, "__traverse__", None) or build_queue(_node, []))
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
                    compose_either_coroutine(
                        node,
                        mapped_scopes.get(node, local_scope),
                        local_scope,
                        collect_either,
                    )
                )

            elif issubclass(node, ResultNode):
                task = asyncio.Task(
                    result_node_compose_coroutine(
                        node,
                        mapped_scopes.get(node, local_scope),
                        futures[node.__from_node__],
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
        mapped_scopes: dict[type["Node"], Scope],
        futures: dict[type["Node"], asyncio.Future] | None = None,
    ):
        validate_local_scope_is_linked_to_node_scopes(local_scope, mapped_scopes)

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

        try:
            results = await asyncio.gather(*final_futures, return_exceptions=True)
        finally:
            # Cancel any still-pending spawned task (a losing concurrent-either branch, a sibling
            # of a failed node) before returning. Cancelling — rather than awaiting to completion —
            # means a loser that blocks indefinitely cannot hang run(), while still preventing an
            # orphan task from waking up after the scope is closed. Awaiting the cancellations also
            # retrieves their exceptions so they are not reported as "never retrieved".
            pending = [future for future in futures.values() if not future.done()]
            for future in pending:
                future.cancel()
            if pending:
                await asyncio.gather(*pending, return_exceptions=True)

        for result in results:
            if isinstance(result, BaseException):
                raise result
            if kungfu.is_err(result):
                raise result.error


__all__ = ("EventLoopAgent",)
