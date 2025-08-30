import pytest

from nodnod import Value
from nodnod.utils.aio import awaitable_noop


class TestValueExtended:
    @pytest.mark.asyncio
    async def test_value_close_with_sync_generator(self):
        def sync_gen():
            yield 1
            yield 2

        gen = sync_gen()
        next(gen)  # Start generator

        value = Value(int, 42, generator=gen)
        result = value.close()

        assert isinstance(result, awaitable_noop)
        assert value.generator is None

    @pytest.mark.asyncio
    async def test_value_close_with_async_generator(self):
        async def async_gen():
            yield 1
            yield 2

        gen = async_gen()
        await gen.__anext__()  # Start generator

        value = Value(int, 42, generator=gen)
        result = await value.close()

        # Generator should be closed
        assert value.generator is None

    def test_value_repr_with_generator(self):
        def gen():
            yield 1

        g = gen()
        value = Value(int, 42, generator=g)
        repr_str = repr(value)

        assert "int" in repr_str
        assert "42" in repr_str
        assert "open generator" in repr_str
        assert next(g) == 1

    def test_value_repr_without_generator(self):
        value = Value(str, "test", generator=None)
        repr_str = repr(value)

        assert "str" in repr_str
        assert "test" in repr_str
        assert "open generator" not in repr_str
