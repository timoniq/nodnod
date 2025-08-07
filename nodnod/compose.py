from nodnod.node import Node, ComposeResponse
from nodnod.scope import Scope
from nodnod.value import Value
from nodnod.error import NodeError
from nodnod.utils.generator import generator_send, generator_asend
import inspect
import typing
import types
import fntypes


async def initialize_node[T](node_cls: type[Node], value: ComposeResponse[T]) -> Value[T]:
    if inspect.isawaitable(value):
        value = typing.cast(T, await value)
    
    if isinstance(value, types.GeneratorType):
        generator = typing.cast(typing.Generator[T, None, None], value)
        value = generator_send(generator).expect("Generator did not generate any value")
        return Value(node_cls, value, generator=generator)
    
    if isinstance(value, types.AsyncGeneratorType):
        generator = typing.cast(typing.AsyncGenerator[T, None], value)
        value = (await generator_asend(generator)).expect("Generator did not generate any value")
        return Value(node_cls, value, generator=generator)
    
    # value is T
    return Value(node_cls, value)  # type: ignore


async def compose_node[T](
    node: type[Node[T]],
    node_scope: Scope,
    local_scope: Scope,
) -> fntypes.Result[Value[T], NodeError]:
    """Composes node into a boxed value.
    If node is already composed in scope, then returns box value from scope"""

    if n := node_scope.retrieve(node):
        return fntypes.Ok(n.unwrap())
    
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

    try:
        value = node.__bound_compose__(dependencies)
        node_scope[node] = await initialize_node(node, value)
    
    except NodeError as e:
        return fntypes.Error(NodeError(f"failed to compose {node.__name__}", from_error=e))

    return fntypes.Ok(node_scope[node])
