from nodnod.error import NodeBuildError
from nodnod.node import Node


def validate_no_circular_dependency(
    final: type[Node],
    parents: list[type[Node]],
    validated: set[type[Node]] | None = None,
) -> None:
    if validated is None:
        validated = set()

    # A node reachable through several paths is validated once: keeps the whole
    # check O(V + E) instead of exponential on shared-subtree (diamond) graphs.
    if final in validated:
        return

    if final in parents:
        raise NodeBuildError(f"Circular dependency {' -> '.join(n.__name__ for n in parents + [final])}")

    dependencies = final.__dependencies__
    if dependencies is None:
        raise NodeBuildError(
            f"`{final.__name__}` is not fully initialized: it has an unresolved forward "
            "reference or a mutually-recursive dependency that could not be built.",
        )

    parents.append(final)
    for dependency in dependencies:
        validate_no_circular_dependency(dependency, parents, validated)
    parents.pop()
    validated.add(final)


__all__ = ("validate_no_circular_dependency",)
