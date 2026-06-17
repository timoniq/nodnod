import typing

from nodnod.builder.validate_graph import validate_no_circular_dependency

if typing.TYPE_CHECKING:
    from nodnod.node import Node, Queue


def build_queue(final: type["Node"], queue: "Queue") -> "Queue":
    """`Depth-first traversal` to compute node compositional order.

    Cycle validation runs once for the whole subtree (memoized inside
    `validate_no_circular_dependency`), and node membership is tracked with a set,
    so queue construction is O(V + E) instead of re-validating at every recursion level.
    """
    validate_no_circular_dependency(final, [])
    _extend_queue(final, queue, set(queue))
    return queue


def _extend_queue(final: type["Node"], queue: "Queue", seen: set[type["Node"]]) -> None:
    if final in seen:
        return

    seen.add(final)
    for dependency in final.__dependencies__:
        _extend_queue(dependency, queue, seen)
    queue.append(final)


def traverse_all(nodes: set[type["Node"]]) -> "Queue":
    all_nodes = list[type["Node"]]()
    for node in nodes:
        build_queue(node, all_nodes)
    return all_nodes


__all__ = ("build_queue", "traverse_all")
