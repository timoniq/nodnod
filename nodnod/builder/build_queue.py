import typing

from nodnod.builder.validate_graph import validate_no_circular_dependency

if typing.TYPE_CHECKING:
    from nodnod.node import Node, Queue


def build_queue(final: type["Node"], queue: "Queue") -> "Queue":
    """`Depth-first traversal` to simply compute node compositional order without any optimizations"""
    validate_no_circular_dependency(final, list())

    for dependency in final.__dependencies__:
        if dependency in queue:
            continue
        build_queue(dependency, queue)
    
    if final not in queue:
        queue.append(final)
    return queue


def traverse_all(nodes: set[type["Node"]]) -> "Queue":
    all_nodes = list[type["Node"]]()
    for node in nodes:
        build_queue(node, all_nodes)
    return all_nodes


__all__ = ("build_queue", "traverse_all")
