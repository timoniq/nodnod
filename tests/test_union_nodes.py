import typing

import kungfu
import pytest

from nodnod import EventLoopAgent, Node, Scope, scalar_node
from nodnod.interface.union_node import create_union_node, is_union


class TestUnionNodes:
    def test_is_union(self):
        class Test(Node, abstract=True): ...

        assert is_union(Test | None)
        assert not is_union(typing.Union)
        assert not is_union(int | Node)
        assert not is_union(int)
        assert not is_union(str)

    def test_create_union_node(self):
        union_type = typing.Union[Node, Node[str]]
        union_node = create_union_node(union_type)

        assert issubclass(union_node, Node)
        assert len(getattr(union_node, "__either__")) == 2

    @pytest.mark.asyncio
    async def test_union_node_basic_usage(self):
        @scalar_node
        class IntNode:
            @classmethod
            def __compose__(cls) -> int:
                return 42

        class StringNode(Node, abstract=True):
            __dependencies__ = set()
            __injections__ = set()

        StringNode.__type__ = StringNode

        @scalar_node
        class ConsumerNode:
            @classmethod
            def __compose__(cls, value: typing.Union[IntNode, StringNode]) -> str:
                assert isinstance(value, int)
                return f"Got int: {value}"

        agent = EventLoopAgent.build({ConsumerNode})  # type: ignore
        scope = Scope(detail="test")

        async with scope:
            await agent.run(local_scope=scope, mapped_scopes={})
            result = scope.retrieve(ConsumerNode)
            assert kungfu.is_some(result)
            assert "Got" in result.unwrap().value
