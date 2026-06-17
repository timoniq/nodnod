import inspect
import types
import typing

import kungfu

from nodnod.error import NodeError
from nodnod.node import ComposeResponse, Node
from nodnod.scope import Scope
from nodnod.utils.generator import generator_asend, generator_send
from nodnod.value import Value


async def initialize_node[T](cls: type[Node], value: ComposeResponse[T]) -> Value[T]:
    if inspect.isawaitable(value):
        value = typing.cast("T", await value)

    if isinstance(value, types.GeneratorType):
        generator = typing.cast("typing.Generator[T, None, None]", value)
        value = generator_send(generator).expect("Generator did not generate any value")
        return Value(cls, value, generator=generator)

    if isinstance(value, types.AsyncGeneratorType):
        generator = typing.cast("typing.AsyncGenerator[T, None]", value)
        value = (await generator_asend(generator)).expect("Generator did not generate any value")
        return Value(cls, value, generator=generator)

    # value is T
    return Value(cls, value)  # type: ignore


async def compose_node[T](
    node: type[Node[T]],
    node_scope: Scope,
    local_scope: Scope,
    winner: Value | None = None,
) -> kungfu.Result[Value[T], NodeError]:
    """Composes node into a boxed value.
    If node is already composed in scope, then returns box value from scope"""

    if n := node_scope.retrieve(node):
        return kungfu.Ok(n.unwrap())

    try:
        if hasattr(node, "__either__"):
            dependencies = _either_dependencies(node, local_scope, winner)
        else:
            # Gathering injected dependencies can raise NodeError (a missing injection). Keep it
            # inside the try so it becomes a soft Error an Either can fall through on, rather than
            # an exception that escapes and aborts the whole resolution.
            dependencies = _node_dependencies(node, local_scope)

        value = node.__initialize__(dependencies)
        node_scope[node] = await initialize_node(node.__type__, value)
    except NodeError as e:
        return kungfu.Error(NodeError(f"failed to compose `{node.__name__}`", from_error=e))

    return kungfu.Ok(node_scope[node])


def _either_dependencies(node: type[Node], local_scope: Scope, winner: Value | None) -> set[Value]:
    if winner is not None:
        return {winner}

    either: tuple[type[Node], ...] = getattr(node, "__either__")
    for candidate in either:
        if dep := local_scope.retrieve(candidate):
            return {dep.unwrap()}

    return set()


def _node_dependencies(node: type[Node], local_scope: Scope) -> set[Value]:
    dependencies = set[Value]()

    for dependency in node.__dependencies__:
        if dep := local_scope.retrieve(dependency):
            dependencies.add(dep.unwrap())

    for injected_type in node.__injections__:
        dependencies.add(
            local_scope
            .retrieve(injected_type)
            .expect(NodeError(f"couldn't inject `{injected_type.__name__}` because it was not set"))
        )

    return dependencies


__all__ = ("compose_node", "initialize_node")
