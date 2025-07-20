from nodnod import Node, LayerAgent, Scope
import asyncio

class A(Node[int]):
    @classmethod
    async def __compose__(cls):
        print("calculating a")
        yield 11
        print("closing A")


class B(Node[int]):
    @classmethod
    async def __compose__(cls):
        print("calculating b")
        yield 5
        print("closing b")


class C(Node[int]):
    @classmethod
    def __compose__(cls, a: A, b: B):
        print("calculating c")
        yield a.value + b.value
        print("close c")


async def main():
    agent = LayerAgent.build({C})

    global_scope = Scope(detail="global")

    async with global_scope.create_child("local") as scope:
        await agent.run(
            local_scope=scope, 
            mapped_scopes={A: global_scope},
        )
        print(scope)

    async with global_scope.create_child("local2") as scope:
        await agent.run(
            local_scope=scope, 
            mapped_scopes={A: global_scope},
        )
        print(global_scope)
        print(scope)

    await global_scope.close()

    # Firstly closes C
    # then A and B (any order because they are from the same layer of parallels)


asyncio.run(main())
