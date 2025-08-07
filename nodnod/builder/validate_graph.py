from nodnod.node import Node
from nodnod.error import NodeBuildError

def validate_no_circular_dependency(final: type[Node], parents: list[type[Node]]) -> None:
    if final in parents:
        raise NodeBuildError(f"Circular dependency {' -> '.join(n.__name__ for n in parents + [final])}")

    parents.append(final)
    for dependency in final.__dependencies__:
        validate_no_circular_dependency(dependency, parents)
    parents.pop()