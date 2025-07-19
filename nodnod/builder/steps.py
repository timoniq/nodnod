import enum
import dataclasses
import typing
from nodnod.node import Node


class StepType(enum.StrEnum):
    PARALLEL = "PARALLEL"
    COMPOSE_ONE = "COMPOSE_ONE"


@dataclasses.dataclass
class Parallel:
    """Listed nodes are interdependent and can be composed in parallel"""
    step_type: typing.Literal[StepType.PARALLEL]
    nodes: set[type[Node]]


@dataclasses.dataclass
class ComposeOne:
    """We have to compose one node"""
    step_type: typing.Literal[StepType.COMPOSE_ONE]
    node: type[Node]


type Step = Parallel | ComposeOne
