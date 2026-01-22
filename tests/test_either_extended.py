import kungfu
import pytest

from nodnod import EventLoopAgent, Scope, scalar_node
from nodnod.interface.either import ConcurrentEither, SequentialEither


class TestEitherExtended:
    @pytest.mark.asyncio
    async def test_either_with_non_scalar_result(self):
        @scalar_node
        class SuccessNode:
            @classmethod
            def __compose__(cls) -> int:
                return 42

        class CustomEither(SequentialEither):
            __either__ = (SuccessNode,)

        agent = EventLoopAgent.build({CustomEither})
        scope = Scope(detail="test")

        async with scope:
            await agent.run(local_scope=scope, mapped_scopes={})
            result = scope.retrieve(CustomEither)
            assert kungfu.is_some(result)
            # Should get the Either instance, not the scalar value
            assert hasattr(result.unwrap().value, "value")

    def test_either_init_subclass_concurrent(self):
        class TestConcurrentEither(ConcurrentEither):
            __either__ = ()

        assert TestConcurrentEither.is_concurrent is True

    def test_either_init_subclass_sequential(self):
        class TestSequentialEither(SequentialEither):
            __either__ = (int, int)

        assert TestSequentialEither.is_concurrent is False
