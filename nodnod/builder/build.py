from nodnod.node import Queue
from nodnod.builder.steps import Step, Parallel, ComposeOne, StepType
from nodnod.builder.build_parallels import build_parallels


def build(nodes: Queue) -> list[Step]:
    """Builds list of nodes to an optimized set of steps required for their computation"""

    parallels = build_parallels(nodes)
    steps: list[Step] = []

    for parallel in parallels:
        if len(parallel) == 1:
            steps.append(ComposeOne(StepType.COMPOSE_ONE, parallel.pop()))
        else:
            steps.append(Parallel(StepType.PARALLEL, parallel))
    
    return steps
