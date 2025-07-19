from nodnod import Node, build, compose_from_steps
import asyncio

class A(Node[int]):
    @classmethod
    async def __compose__(cls):
        yield 11
        print("closing A")


class B(Node[int]):
    @classmethod
    async def __compose__(cls):
        yield 5
        print("closing b")


class C(Node[int]):
    @classmethod
    def __compose__(cls, a: A, b: B):
        yield a.value + b.value
        print("close c")


async def main():
    steps = build({C})
    print(steps)

    scope = await compose_from_steps(steps, {})
    print(scope)

    await scope.close()

    # Firstly closes C
    # then A and B (any order because they are from the same layer of parallels)


asyncio.run(main())
