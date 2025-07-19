import enum
import dataclasses
import typing
from nodnod.node import Node


class StepType(enum.StrEnum):
    PARALLEL = "PARALLEL"


@dataclasses.dataclass
class Parallel:
    step_type: typing.Literal[StepType.PARALLEL]
    nodes: set[type[Node]]


type Step = Parallel