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
) -> kungfu.Result[Value[T], NodeError]:
    """Composes node into a boxed value.
    If node is already composed in scope, then returns box value from scope"""

    if n := node_scope.retrieve(node):
        return kungfu.Ok(n.unwrap())

    dependencies = set[Value]()

    dependency_nodes = getattr(
        node,
        "__either__",
        node.__dependencies__
    )

    for dependency in dependency_nodes:
        # dependency can not exist for nodes in __either__ field
        if dep := local_scope.retrieve(dependency):
            dependencies.add(
                dep.unwrap()
            )

    for injected_type in node.__injections__:
        dependencies.add(
            local_scope
            .retrieve(injected_type)
            .expect(NodeError(f"couldn't inject `{injected_type.__name__}` because it was not set"))
        )

    try:
        value = node.__initialize__(dependencies)
        node_scope[node] = await initialize_node(node.__type__, value)
    except NodeError as e:
        return kungfu.Error(NodeError(f"failed to compose `{node.__name__}`", from_error=e))

    return kungfu.Ok(node_scope[node])


__all__ = ("compose_node", "initialize_node")
