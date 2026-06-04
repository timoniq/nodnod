# type: ignore

import asyncio
import dataclasses
import typing

import kungfu

from nodnod import (
    DataNode,
    EventLoopAgent,
    Node,
    NodeConstructor,
    NodeError,
    Scalar,
    Scope,
    SequentialEither,
    Value,
    case,
    generic_node,
    polymorphic,
    scalar_node,
)
from nodnod.utils.prepare_values import prepare_values


@generic_node
# @dataclasses.dataclass
class Lolik[T: (str, int), *Ts, X: str | int](DataNode, abstract=True):
    def __init__(self, t: T, x: X):
        self.t = t
        self.x = x

    @classmethod
    async def __compose__(cls, t: type[T], y: type[X]) -> typing.Self:
        return cls(t("11"), y("22"))


@generic_node
class TypeArgs[*Ts]:
    def __init__(self, type_args: tuple[typing.Unpack[Ts]]) -> None:
        self.type_args = type_args

    @classmethod
    def __compose__(cls, type_args: tuple[typing.Unpack[Ts]]) -> typing.Self:
        return cls(type_args)


class Interface:
    def get_lol(self) -> str: ...


class MyInterface:
    def get_lol(self) -> str:
        return "megalol"


@scalar_node
class A:
    @classmethod
    async def __compose__(cls):
        yield int(11)


@scalar_node
class Bitchnode:
    @classmethod
    async def __compose__(cls):
        raise NodeError("dang")


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


@scalar_node
class Lol:
    @classmethod
    def __compose__(cls, i: Interface) -> str:
        return i.get_lol()


class MyNode(Node):
    def __init__(self):
        self.bro = 3


@scalar_node
class LOL:
    @classmethod
    def __compose__(
        cls,
        x: Lol,
        mi: MyInt,
        opt: kungfu.Option[A],
        ar: kungfu.Result[Bitchnode, Exception],
    ) -> str:
        return x.upper() * mi + "d"


@scalar_node
class Jackpot:
    @classmethod
    def __compose__(cls) -> int:
        return 777


class MultiplyBy(NodeConstructor):
    def __init__(self, multiplier: int = 5) -> None:
        self.multiplier = multiplier

    def __compose__(self, jackpot: Jackpot) -> int:
        return 123 * self.multiplier + jackpot


@scalar_node
class Sum:
    @classmethod
    def __compose__(cls, a: Scalar[int, MultiplyBy], b: Scalar[int, MultiplyBy[10]]) -> int:
        return a + b


async def main():
    agent = EventLoopAgent.build({TypeArgs[int, str], LOL, C, Lolik[str, float, str], Lolik[int, str, int], Sum})  # type: ignore

    global_scope = Scope(detail="global")
    global_scope.push(Value(Interface, MyInterface()))

    async with global_scope.create_child("local") as scope:
        await agent.run(
            local_scope=scope,
            mapped_scopes={A: global_scope},
        )
        print(prepare_values(scope.merge()))

    await global_scope.close()

    # Firstly closes C
    # then A and B (any order because they are from the same layer of parallels)


asyncio.run(main())
