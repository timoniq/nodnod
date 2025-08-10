import asyncio
import dataclasses

from nodnod import DataNode, EventLoopAgent, Node, NodeError, Scope, Value, case, polymorphic, scalar_node
from nodnod.interface.either import ConcurrentEither, SequentialEither
from nodnod.interface.polymorphic import case, polymorphic
from nodnod.utils.prepare_values import prepare_values


class Interface:
    def get_lol(self) -> str:
        ...


class MyInterface:
    def get_lol(self) -> str:
        return "megalol"


@scalar_node
class A:
    @classmethod
    async def __compose__(cls):
        yield int(11)


@scalar_node
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
        return b


@dataclasses.dataclass
class C(DataNode):
    x: float
    y: float

    @classmethod
    def __compose__(cls, aorb: AorB):
        print(aorb)
        print("calculating c")
        print(aorb.value)
        return cls(1.2, aorb.value / 2)
        print("close c")


@scalar_node
class Lol:
    @classmethod
    def __compose__(cls, i: Interface) -> str:
        return i.get_lol()


@scalar_node
class LOL:
    @classmethod
    def __compose__(cls, x: Lol, mi: MyInt) -> str:
        print(x, mi)
        return x.upper() * mi


async def main():
    agent = EventLoopAgent.build({LOL, C})

    global_scope = Scope(detail="global")
    global_scope.push(Value(Interface, MyInterface()))

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
