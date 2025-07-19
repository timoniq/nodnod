from nodnod import Node, build, compose_from_steps
import asyncio

class A(Node[int]):
    @classmethod
    def __compose__(cls) -> int:
        return 11


class B(Node[int]):
    @classmethod
    def __compose__(cls) -> int:
        return 5


class C(Node[int]):
    @classmethod
    def __compose__(cls, a: A, b: B) -> int:
        return a.value + b.value
    
    @classmethod
    def __dependencies__(cls) -> set[type[Node]]:
        return {A, B}


async def main():
    steps = build({C})
    print(steps)

    scope = await compose_from_steps(steps, {})
    print(scope)


asyncio.run(main())
