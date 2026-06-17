from typing import Self
from nodnod.agent.layer.steps import Step, Parallel, Single, StepType
from nodnod.builder.build_parallels import build_parallels

from nodnod.agent.base import Agent
from nodnod.node import Node
from nodnod.scope import Scope, validate_local_scope_is_linked_to_node_scopes
from nodnod.error import NodeError
from nodnod.value import Value
import asyncio
import kungfu


def build_steps(nodes: set[type[Node]]) -> list[Step]:
    """Builds list of nodes to an optimized set of steps required for their computation"""

    parallels = build_parallels(nodes)
    steps: list[Step] = []

    for parallel in parallels:
        if len(parallel) == 1:
            steps.append(Single(StepType.SINGLE, parallel.pop()))
        else:
            steps.append(Parallel(StepType.PARALLEL, parallel))

    return steps


class LayerAgent(Agent):
    """Composes in isolated layers"""

    def __init__(self, steps: list[Step]):
        self.steps = steps

    @classmethod
    def build(cls, nodes: set[type[Node]]) -> Self:
        return cls(steps=build_steps(nodes))

    async def run(
        self,
        local_scope: Scope,
        mapped_scopes: dict[type[Node], Scope],
    ):
        from nodnod.compose import compose_node

        validate_local_scope_is_linked_to_node_scopes(local_scope, mapped_scopes)
        initiations = dict[type[Node], kungfu.Result[Value[type[Node]], NodeError]]()

        for step in self.steps:
            match step:

                case Parallel(nodes=nodes):
                    coros = [
                        compose_node(node, mapped_scopes.get(node, local_scope), local_scope)
                        for node in nodes
                    ]
                    results = await asyncio.gather(*coros, return_exceptions=True)

                    for i, node in enumerate(nodes):
                        result = results[i]
                        # A cancelled/raised coroutine surfaces as a BaseException (CancelledError
                        # is a BaseException, not Exception) — re-raise instead of swallowing it.
                        if isinstance(result, BaseException):
                            raise result
                        # compose_node signals failure by returning a falsy kungfu.Error, not by
                        # raising; propagate it like EventLoopAgent.run does.
                        if kungfu.is_err(result):
                            raise result.error

                        initiations[node] = result  # type: ignore

                case Single(node=node):
                    result = await compose_node(node, mapped_scopes.get(node, local_scope), local_scope)
                    if kungfu.is_err(result):
                        raise result.error
                    initiations[node] = result
