from nodnod.node import Node, ComposeResponse
from nodnod.scope import Scope
from nodnod.box import Box
from nodnod.error import NodeError
from nodnod.builder.steps import Step
from nodnod.agent.aio import AsyncAgent
from nodnod.utils import generator_send, generator_asend
import inspect
import typing
import types


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
) -> Box[T]:
    """Composes node into a boxed value.
    If node is already composed in scope, then returns box value from scope"""

    if box := scope.retrieve(node):
        return box.unwrap()
    
    dependencies = []
    for dependency in node.__dependencies__:
        dependencies.append(
            scope.retrieve(dependency).expect(NodeError("Dependency was not resolved"))
        )
    
    value = node.__compose__(*dependencies)
    
    scope[node] = await create_node(node, value)

    return scope[node].__box__()


async def compose_from_steps(
    steps: list[Step],
    node_scopes: dict[type[Node], Scope],
) -> Scope:
    agent = AsyncAgent(steps)
    local_scope = Scope()  # FIXME
    await agent.run(local_scope, node_scopes)
    return local_scope
