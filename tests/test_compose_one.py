import pytest

from nodnod import scalar_node
from nodnod.interface.compose_one import compose_one


class TestComposeOne:
    @pytest.mark.asyncio
    async def test_compose_one_simple_node(self):
        @scalar_node
        class SimpleNode:
            @classmethod
            def __compose__(cls) -> int:
                return 42

        result = await compose_one(SimpleNode)
        assert result == 42

    @pytest.mark.asyncio
    async def test_compose_one_with_injections(self):
        class Config:
            value: int = 100

        @scalar_node
        class NodeWithInjection:
            @classmethod
            def __compose__(cls, config: Config) -> int:
                return config.value

        config = Config()
        result = await compose_one(NodeWithInjection, injections={Config: config})
        assert result == 100

    @pytest.mark.asyncio
    async def test_compose_one_with_dependencies(self):
        @scalar_node
        class DepNode:
            @classmethod
            def __compose__(cls) -> int:
                return 10

        @scalar_node
        class MainNode:
            @classmethod
            def __compose__(cls, dep: DepNode) -> int:
                return dep * 2

        result = await compose_one(MainNode)
        assert result == 20

    @pytest.mark.asyncio
    async def test_compose_one_with_multiple_injections(self):
        class ConfigA:
            value: int = 10

        class ConfigB:
            value: int = 20

        @scalar_node
        class NodeWithMultipleInjections:
            @classmethod
            def __compose__(cls, a: ConfigA, b: ConfigB) -> int:
                return a.value + b.value

        result = await compose_one(
            NodeWithMultipleInjections,
            injections={ConfigA: ConfigA(), ConfigB: ConfigB()}
        )
        assert result == 30

    @pytest.mark.asyncio
    async def test_compose_one_with_none_injections(self):
        @scalar_node
        class SimpleNode2:
            @classmethod
            def __compose__(cls) -> str:
                return "hello"

        result = await compose_one(SimpleNode2, injections=None)
        assert result == "hello"

    @pytest.mark.asyncio
    async def test_compose_one_with_empty_injections(self):
        @scalar_node
        class SimpleNode3:
            @classmethod
            def __compose__(cls) -> str:
                return "world"

        result = await compose_one(SimpleNode3, injections={})
        assert result == "world"
