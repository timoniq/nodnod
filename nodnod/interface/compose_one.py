from __future__ import annotations

import typing

if typing.TYPE_CHECKING:
    from nodnod.node import Node

from nodnod.agent.event_loop.agent import Agent, EventLoopAgent
from nodnod.interface.agent_from_node import create_agent_from_node
from nodnod.interface.inject import inject_internals
from nodnod.scope import Scope


async def compose_one[T](
    node: type[Node[T]],
    injections: dict[typing.Any, typing.Any] | None = None,
    mapped_scopes: dict[type[Node], Scope] | None = None,
    agent_cls: type[Agent] = EventLoopAgent,
) -> T:
    agent = create_agent_from_node(node, agent_cls=agent_cls)

    async with Scope(detail=f"scope for {node.__name__}") as scope:
        inject_internals(scope, internals=injections or {})
        await agent.run(scope, mapped_scopes=mapped_scopes or {})
        return scope[node].value


__all__ = ("compose_one",)
