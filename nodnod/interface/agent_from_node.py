from __future__ import annotations

import typing

from nodnod.agent.event_loop.agent import EventLoopAgent

if typing.TYPE_CHECKING:
    from nodnod.agent.base import Agent
    from nodnod.node import Node


def create_agent_from_node[T: Agent](node: type[Node], agent_cls: type[T] = EventLoopAgent) -> T:
    return agent_cls.build({node})


__all__ = ("create_agent_from_node",)
