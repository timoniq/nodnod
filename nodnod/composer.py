from nodnod.node import Node, ComposeResponse
from nodnod.scope import Scope
from nodnod.box import Box
from nodnod.error import NodeError
from nodnod.utils.generator import generator_send, generator_asend
import inspect
import typing
import types
import fntypes


async def create_node[T](node_cls: type[Node], value: ComposeResponse[T]) -> Node[T]:
    if inspect.isawaitable(value):
        value = typing.cast(T, await value)
    
    if isinstance(value, types.GeneratorType):
        generator = typing.cast(typing.Generator[T, None, None], value)
        value = generator_send(generator).expect("Generator did not generate any value")
        return node_cls(value, generator=generator)
    
    if isinstance(value, types.AsyncGeneratorType):
        generator = typing.cast(typing.AsyncGenerator[T, None], value)
        value = (await generator_asend(generator)).expect("Generator did not generate any value")
        return node_cls(value, generator=generator)

    return node_cls(value)


async def compose_node[T](
    node: type[Node[T]],
    scope: Scope,
) -> fntypes.Result[Box[T], NodeError]:
    """Composes node into a boxed value.
    If node is already composed in scope, then returns box value from scope"""

    if n := scope.retrieve(node):
        return fntypes.Ok(n.unwrap().__box__())
    
    dependencies = set[Node]()
    for dependency in node.__dependencies__:
        dependencies.add(
            scope
            .retrieve(dependency)
            .expect(NodeError("Dependency was not resolved"))
        )
    
    try:
        value = node.__bound_compose__(dependencies)
        scope[node] = await create_node(node, value)
    
    except NodeError as e:
        return fntypes.Error(e)

    return fntypes.Ok(scope[node].__box__())
