from nodnod.interface.node_from_function import create_agent_from_node
from nodnod.agent.event_loop.agent import EventLoopAgent, Agent
from nodnod.scope import Scope
from nodnod.node import Node
import typing


async def compose_one[T](
    node: type[T],
    injections: dict[type[typing.Any], typing.Any] | None = None,
    mapped_scopes: dict[type, Scope] | None = None,
    agent_cls: type[Agent] = EventLoopAgent,
) -> T:
    if not injections:
        injections = {}
    
    agent = create_agent_from_node(node, agent_cls=agent_cls)  # type: ignore
    async with Scope(detail=f"scope for {node.__name__}") as scope:
        for t, v in injections.items():
            scope.inject(t, v)
        await agent.run(scope, mapped_scopes=mapped_scopes or {})
        return scope[node].value


__all__ = ("compose_one",)
