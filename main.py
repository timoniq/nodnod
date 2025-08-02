import asyncio

from nodnod import EventLoopAgent, Node, NodeError, Scope
from nodnod.interface.either import ConcurrentEither, SequentialEither
from nodnod.utils.prepare_values import prepare_values
from nodnod.interface.scalar import scalar_node

from nodnod.interface.polymorphic import polymorphic, case



@scalar_node
class A:
    @classmethod
    async def __compose__(cls):
        yield int(11)


class B(Node[int]):
    @classmethod
    async def __compose__(cls):
        yield 5


class AorB(SequentialEither):
    __either__ = (A, B)


@scalar_node
@polymorphic[int]
class MyInt:
    @case
    def from_a(cls, a: A) -> int:
        return a + 8
    
    @case
    def from_b(cls, b: B) -> int:
        return b.value


class C(Node[int]):
    @classmethod
    def __compose__(cls, aorb: AorB):
        print(aorb)
        print("calculating c")
        yield aorb.value.v.value
        print("close c")


@scalar_node
class Lol:
    @classmethod
    def __compose__(cls) -> str:
        return "hello"


@scalar_node
class LOL:
    @classmethod
    def __compose__(cls, x: Lol, mi: MyInt) -> str:
        print(x, mi)
        return x.upper() * mi


async def main():
    agent = EventLoopAgent.build({C, LOL})

    global_scope = Scope(detail="global")

    async with global_scope.create_child("local") as scope:
        await agent.run(
            local_scope=scope, 
            mapped_scopes={A: global_scope},
        )
        print(prepare_values(scope.merge()))

    # async with global_scope.create_child("local2") as scope:
    #     await agent.run(
    #         local_scope=scope, 
    #         mapped_scopes={A: global_scope},
    #     )
    #     print(global_scope)
    #     print(scope)

    await global_scope.close()

    # Firstly closes C
    # then A and B (any order because they are from the same layer of parallels)


asyncio.run(main())
