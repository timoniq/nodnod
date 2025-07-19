from nodnod.builder.steps import Step
from nodnod.node import Node
from nodnod.scope import Scope

class Agent:
    def __init__(self, steps: list[Step]):
        self.steps = steps
    
    def run(self, node_scopes: dict[type[Node], Scope]):
        ...
