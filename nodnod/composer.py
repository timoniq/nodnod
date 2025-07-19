from nodnod.node import Node, ComposeResponse
from nodnod.scope import Scope
from nodnod.box import Box
from nodnod.error import NodeError
from nodnod.builder.steps import Step
from nodnod.agent.aio import AsyncAgent
from nodnod.utils.generator import generator_send, generator_asend
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

    if n := scope.retrieve(node):
        return n.unwrap().__box__()
    
    dependencies = set[Node]()
    for dependency in node.__dependencies__:
        dependencies.add(
            scope
            .retrieve(dependency)
            .expect(NodeError("Dependency was not resolved"))
        )
    
    value = node.__bound_compose__(dependencies)
    
    scope[node] = await create_node(node, value)

    return scope[node].__box__()


def validate_local_scope_is_linked_to_node_scopes(local_scope: Scope, node_scopes: dict[type[Node], Scope]):
    if __debug__:
        for node, node_scope in node_scopes.items():
            if not local_scope.has_parent(node_scope):
                raise NodeError(f"`{node.__name__}`'s scope ({node_scope.detail}) is not a parent of local scope ({local_scope.detail})")


async def compose_from_steps(
    steps: list[Step],
    *,
    local_scope: Scope,
    node_scopes: dict[type[Node], Scope] | None = None,
):
    node_scopes = node_scopes or {}
    validate_local_scope_is_linked_to_node_scopes(local_scope, node_scopes)

    agent = AsyncAgent(steps)
    await agent.run(local_scope, node_scopes)
