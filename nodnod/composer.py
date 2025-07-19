from nodnod.node import Node
from nodnod.scope import Scope
from nodnod.box import Box
from nodnod.error import NodeError
from nodnod.builder.steps import Step
from nodnod.agent.aio import AsyncAgent


async def compose_node[T](
    node: type[Node[T]],
    scope: Scope,
) -> Box[T]:
    
    if box := scope.retrieve(node):
        return box.unwrap()
    
    dependencies = []
    for dependency in node.__dependencies__():
        dependencies.append(
            scope.retrieve(dependency).expect(NodeError("Dependency was not resolved"))
        )
    
    value = node.__compose__(*dependencies)
    scope[node] = node(value)
    return scope[node].__box__()


async def compose_from_steps(
    steps: list[Step],
    node_scopes: dict[type[Node], Scope],
) -> Scope:
    agent = AsyncAgent(steps)
    local_scope = Scope()  # FIXME
    await agent.run(local_scope, node_scopes)
    return local_scope
