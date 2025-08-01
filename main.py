import asyncio

from nodnod import EventLoopAgent, Node, NodeError, Scope
from nodnod.interface.either import ConcurrentEither, SequentialEither
from nodnod.utils.prepare_values import prepare_values
from nodnod.interface.scalar import scalar_node


@scalar_node
class A:
    @classmethod
    async def __compose__(cls):
        print("calculating a")
        # raise NodeError("im error")
        yield 11
        print("closing A")


class B(Node[int]):
    @classmethod
    async def __compose__(cls):
        print("calculating b (should never)")
        # raise NodeError("im lol error")
        yield 5
        print("closing b")


class AorB(SequentialEither):
    __either__ = (A, B)


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
    def __compose__(cls, x: Lol) -> str:
        return x.upper()


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
