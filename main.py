from nodnod import Node, build, compose_from_steps
import asyncio

class A(Node[int]):
    @classmethod
    def __compose__(cls):
        yield 11
        print("closing A")


class B(Node[int]):
    @classmethod
    async def __compose__(cls):
        yield 5
        print("closing b")


class C(Node[int]):
    __dependencies__ = {A, B}
    
    @classmethod
    def __compose__(cls, a: A, b: B) -> int:
        return a.value + b.value


async def main():
    steps = build({C})
    print(steps)

    scope = await compose_from_steps(steps, {})
    print(scope)

    await scope.close()


asyncio.run(main())
