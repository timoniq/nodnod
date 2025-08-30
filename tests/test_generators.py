import fntypes
import pytest

from nodnod.utils.generator import generator_asend, generator_send


class TestGeneratorUtils:
    def test_generator_send_with_value(self):
        def simple_generator():
            yield "first"

        gen = simple_generator()

        result = generator_send(gen)
        assert fntypes.is_some(result)
        assert result.unwrap() == "first"

    def test_generator_send_exhausted(self):
        def empty_generator():
            return
            yield "never reached"

        gen = empty_generator()

        result = generator_send(gen)
        assert fntypes.is_nothing(result)

    @pytest.mark.asyncio
    async def test_generator_asend_with_value(self):
        async def simple_async_generator():
            yield "first"

        gen = simple_async_generator()

        result = await generator_asend(gen)
        assert fntypes.is_some(result)
        assert result.unwrap() == "first"

    @pytest.mark.asyncio
    async def test_generator_asend_exhausted(self):
        async def empty_async_generator():
            return
            yield "never reached"

        gen = empty_async_generator()

        result = await generator_asend(gen)
        assert fntypes.is_nothing(result)
