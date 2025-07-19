from nodnod.node import Queue
from nodnod.builder.steps import Step, Parallel, StepType
from nodnod.builder.build_parallels import build_parallels


def build(nodes: Queue) -> list[Step]:
    parallels = build_parallels(nodes)
    steps = [Parallel(StepType.PARALLEL, parallel) for parallel in parallels]
    return steps