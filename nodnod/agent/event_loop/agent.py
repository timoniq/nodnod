from typing import Self
from nodnod.agent.base import Agent
from nodnod.node import Node
from nodnod.scope import Scope
from nodnod.error import NodeError
from nodnod.box import Box
import asyncio
import fntypes


class EventLoopAgent(Agent):
    def __init__(self) -> None:
        pass

    @classmethod
    def build(cls, nodes: set[type[Node]]) -> Self:
        return cls()
    
    async def run(
        self, 
        local_scope: Scope, 
        mapped_scopes: dict[type[Node], Scope]
    ):
        ...
