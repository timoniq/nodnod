import fntypes
import pytest

from nodnod import Node, NodeError, Scope, Value, scalar_node
from nodnod.compose import compose_node, initialize_node


class TestCompose:
    @pytest.mark.asyncio
    async def test_compose_simple_node(self):
        @scalar_node
        class SimpleNode:
            @classmethod
            def __compose__(cls) -> int:
                return 42

        scope = Scope(detail="test")
        result = await compose_node(SimpleNode, scope, scope)

        assert fntypes.is_ok(result)
        value = result.unwrap()
        assert value.value == 42

    @pytest.mark.asyncio
    async def test_compose_node_with_error(self):
        @scalar_node
        class ErrorNode:
            @classmethod
            def __compose__(cls) -> int:
                raise NodeError("Test error")

        scope = Scope(detail="test")
        result = await compose_node(ErrorNode, scope, scope)

        assert fntypes.is_err(result)
        assert isinstance(result.error, NodeError)

    @pytest.mark.asyncio
    async def test_compose_cached_node(self):
        class CachedNode(Node, abstract=True):
            __dependencies__ = set()
            __injections__ = set()

        CachedNode.__type__ = CachedNode

        scope = Scope(detail="test")
        # Pre-populate the scope
        scope.push(Value(CachedNode, 123))

        result = await compose_node(CachedNode, scope, scope)

        assert fntypes.is_ok(result)
        # Should return cached value, not newly computed
        assert result.unwrap().value == 123

    @pytest.mark.asyncio
    async def test_initialize_node_simple_value(self):
        class TestNode(Node, abstract=True):
            __dependencies__ = set()
            __injections__ = set()

        TestNode.__type__ = TestNode
        value = await initialize_node(TestNode, 42)
        assert isinstance(value, Value)
        assert value.cls == TestNode
        assert value.value == 42

    @pytest.mark.asyncio
    async def test_initialize_node_awaitable(self):
        class TestNode(Node, abstract=True):
            __dependencies__ = set()
            __injections__ = set()

        TestNode.__type__ = TestNode

        async def async_value():
            return "awaitable_result"

        value = await initialize_node(TestNode, async_value())
        assert value.value == "awaitable_result"

    @pytest.mark.asyncio
    async def test_initialize_node_with_sync_generator(self):
        class TestNode(Node, abstract=True):
            __dependencies__ = set()
            __injections__ = set()

        TestNode.__type__ = TestNode

        def gen():
            yield 123

        generator = gen()
        value = await initialize_node(TestNode, generator)
        assert value.value == 123
        assert value.generator is generator

    @pytest.mark.asyncio
    async def test_initialize_node_with_async_generator(self):
        class TestNode(Node, abstract=True):
            __dependencies__ = set()
            __injections__ = set()

        TestNode.__type__ = TestNode

        async def agen():
            yield 456

        generator = agen()
        value = await initialize_node(TestNode, generator)
        assert value.value == 456
        assert value.generator is generator
