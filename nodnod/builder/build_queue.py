from nodnod.node import Node, Queue


def build_queue(final: type[Node], queue: Queue) -> Queue:
    """`Depth-first traversal` to simply compute node compositional order without any optimizations"""

    for dependency in final.__dependencies__():
        if dependency in queue:
            continue
        build_queue(dependency, queue)
    
    queue.add(final)
    return queue
