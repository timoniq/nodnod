from __future__ import annotations

import typing


def repr_node_error(node_error: NodeError, indent: int = 0) -> str:
    prefix = "  " * indent

    if node_error.from_error:
        current = f"{prefix}{node_error.detail}"
        child = repr_node_error(node_error.from_error, indent=indent + 1)
        return f"{current}\n{prefix}  ← {child[len(prefix)+2:]}"

    if node_error.from_many:
        current = f"{prefix}{node_error.detail}"
        lines = [current]
        for error in node_error.from_many:
            child_repr = repr_node_error(error, indent=indent + 1)
            lines.append(f"{prefix}  * {child_repr[len(prefix)+2:]}")
        return "\n".join(lines)

    return f"{prefix}{node_error.detail}"


class NodeError(Exception):
    def __init__(
        self, 
        *detail: typing.Any, 
        from_error: NodeError | None = None,
        from_many: typing.Sequence[NodeError] | None = None,
    ) -> None:
        if from_error and from_many:
            raise RuntimeError("NodeError can either have from_error or from_many")

        self.detail = " ".join(map(str, detail))
        self.from_error = from_error
        self.from_many = from_many

    def __str__(self) -> str:
        return "\n\n" + repr_node_error(self)
    

class NodeBuildError(NodeError):
    pass
