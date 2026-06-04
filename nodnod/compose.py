import inspect
import types
import typing

import kungfu

from nodnod.error import NodeError
from nodnod.node import ComposeResponse, Node
from nodnod.scope import Scope
from nodnod.utils.generator import generator_asend, generator_send
from nodnod.value import Value


async def initialize_node[T](cls: type[Node], response: ComposeResponse[T]) -> Value[T]:
    if inspect.isawaitable(response):
        response = await response

    if isinstance(response, types.GeneratorType):
        generator = typing.cast("typing.Generator[T, None, None]", response)
        value = generator_send(generator).expect("Generator did not generate any value")
        return Value(cls, value, generator=generator)

    if isinstance(response, types.AsyncGeneratorType):
        generator = typing.cast("typing.AsyncGenerator[T, None]", response)
        value = (await generator_asend(generator)).expect("Generator did not generate any value")
        return Value(cls, value, generator=generator)

    return Value(cls, typing.cast("T", response))


async def compose_node[T](
    node: type[Node[T]],
    node_scope: Scope,
    local_scope: Scope,
) -> kungfu.Result[Value[T], NodeError]:
    """Composes node into a boxed value.
    If node is already composed in scope, then returns box value from scope."""

    if n := node_scope.retrieve(node):
        # cast a retrieved box value as Ok
        return n.cast()

    is_either = hasattr(node, "__either__")
    dependency_nodes = getattr(
        node,
        "__either__",
        node.__dependencies__,
    )
    dependencies = set[Value]()

    for dependency in dependency_nodes:
        # dependency can not exist for nodes in __either__ field
        if dep := local_scope.retrieve(dependency):
            dependencies.add(dep.unwrap())

            # one of the candidate dependencies was found, so no further lookup is needed
            if is_either:
                break

    for injected_type in node.__injections__:
        # injection by type is not required for `either` node
        if is_either:
            break

        dependencies.add(
            local_scope.retrieve(injected_type).expect(
                NodeError(f"couldn't inject `{injected_type.__name__}` because it was not set")
            )
        )

    try:
        response = node.__initialize__(dependencies)
        node_scope[node] = value = await initialize_node(node.__type__, response)
    except NodeError as e:
        return kungfu.Error(NodeError(f"failed to compose `{node.__name__}`", from_error=e))

    # returns a composed value
    return kungfu.Ok(value)


__all__ = ("compose_node", "initialize_node")
