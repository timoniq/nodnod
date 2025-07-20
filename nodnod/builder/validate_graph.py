from nodnod.node import Node
from nodnod.error import NodeBuildError

def validate_no_circular_dependency(final: type[Node], parents: list[type[Node]]) -> None:
    parents.append(final)

    for dependency in final.__dependencies__:
        if dependency in parents:
            raise NodeBuildError(f"Circular dependency {dependency.__name__} in {final.__name__}")
        validate_no_circular_dependency(dependency, parents)
