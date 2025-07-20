from nodnod.node import Node
from nodnod.scope import Scope
import typing

class Agent:
    @classmethod
    def build(cls, nodes: set[type[Node]]) -> typing.Self:
        ...

    def run(self, local_scope: Scope, mapped_scopes: dict[type[Node], Scope]):
        ...
