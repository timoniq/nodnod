from nodnod.builder.build_queue import build_queue
import collections
from nodnod.node import Node


def build_parallels(nodes: set[type[Node]]) -> list[set[type[Node]]]:
    """Computes isolated layers of nodes that can be composed in parallel"""
    
    initiators = collections.defaultdict[type[Node], set[type[Node]]](set)
    initiation = dict[type[Node], int]()
    all_nodes = list[type[Node]]()

    for node in nodes:
        build_queue(node, all_nodes)

    for node in all_nodes:
        dependencies = node.__dependencies__
        for dependency in dependencies:
            initiators[dependency].add(node)
        initiation[node] = len(dependencies)
    
    parallels = list[set[type[Node]]]()

    queue = collections.deque([node for node in all_nodes if initiation.get(node, 0) == 0])

    while queue:
        current_layer = set(queue)
        parallels.append(current_layer)

        next_queue = collections.deque()

        for node in current_layer:
            for neighbor in initiators[node]:
                initiation[neighbor] -= 1
                if initiation[neighbor] == 0:
                    next_queue.append(neighbor)

        queue = next_queue

    return parallels
