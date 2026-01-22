import pytest

from nodnod.utils.aio import awaitable_noop, maybe_awaitable


class TestMaybeAwaitable:
    @pytest.mark.asyncio
    async def test_maybe_awaitable_with_regular_value(self):
        result = await maybe_awaitable(42)
        assert result == 42

    @pytest.mark.asyncio
    async def test_maybe_awaitable_with_string(self):
        result = await maybe_awaitable("hello")
        assert result == "hello"

    @pytest.mark.asyncio
    async def test_maybe_awaitable_with_coroutine(self):
        async def async_value():
            return "awaited"

        result = await maybe_awaitable(async_value())
        assert result == "awaited"

    @pytest.mark.asyncio
    async def test_maybe_awaitable_with_async_returning_int(self):
        async def get_number():
            return 123

        result = await maybe_awaitable(get_number())
        assert result == 123

    @pytest.mark.asyncio
    async def test_maybe_awaitable_with_none(self):
        result = await maybe_awaitable(None)
        assert result is None

    @pytest.mark.asyncio
    async def test_maybe_awaitable_with_async_none(self):
        async def get_none():
            return None

        result = await maybe_awaitable(get_none())
        assert result is None


class TestAwaitableNoop:
    @pytest.mark.asyncio
    async def test_awaitable_noop_returns_none(self):
        noop = awaitable_noop()
        result = await noop
        assert result is None or result == ()

    def test_awaitable_noop_has_await(self):
        noop = awaitable_noop()
        assert hasattr(noop, "__await__")

    def test_awaitable_noop_await_returns_generator(self):
        noop = awaitable_noop()
        gen = noop.__await__()
        assert hasattr(gen, "__next__") or hasattr(gen, "__iter__")
