import pytest

from nodnod import Scope, Value, Node


class TestScopeRepr:
    def test_empty_scope_repr(self):
        scope = Scope(detail="empty")
        scope.clear()

        repr_str = repr(scope)
        assert "empty" in repr_str
        assert "(empty)" in repr_str

    def test_scope_repr_with_values(self):
        class TestNode(Node, abstract=True):
            __dependencies__ = set()
            __injections__ = set()

        TestNode.__type__ = TestNode

        scope = Scope(detail="test")
        scope.push(Value(TestNode, 42))

        repr_str = repr(scope)
        assert "test" in repr_str
        assert "TestNode" in repr_str

    @pytest.mark.asyncio
    async def test_scope_close_with_multiple_async_values(self):
        class AsyncValue1:
            def __init__(self):
                self.closed = False

            async def close(self):
                self.closed = True

        class AsyncValue2:
            def __init__(self):
                self.closed = False

            async def close(self):
                self.closed = True

        scope = Scope(detail="async_test")
        obj1 = AsyncValue1()
        obj2 = AsyncValue2()

        async def async_gen1():
            yield obj1
            await obj1.close()

        async def async_gen2():
            yield obj2
            await obj2.close()

        gen1 = async_gen1()
        await gen1.__anext__()
        gen2 = async_gen2()
        await gen2.__anext__()

        scope.push(Value(AsyncValue1, obj1, generator=gen1))
        scope.push(Value(AsyncValue2, obj2, generator=gen2))

        await scope.close()
        assert obj1.closed
        assert obj2.closed
        assert scope.is_closed
