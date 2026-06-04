import dataclasses
import enum
import typing

from nodnod.node import Node


class StepType(enum.StrEnum):
    PARALLEL = "PARALLEL"
    SINGLE = "SINGLE"


@dataclasses.dataclass
class Parallel:
    """Listed nodes are interdependent and can be composed in parallel"""

    step_type: typing.Literal[StepType.PARALLEL]
    nodes: set[type[Node]]


@dataclasses.dataclass
class Single:
    """We have to compose one node"""

    step_type: typing.Literal[StepType.SINGLE]
    node: type[Node]


type Step = Parallel | Single
