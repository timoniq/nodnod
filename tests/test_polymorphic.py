import fntypes
import pytest

from nodnod import EventLoopAgent, Scope, scalar_node
from nodnod.interface.polymorphic import case, polymorphic


class TestPolymorphic:
    @pytest.mark.asyncio
    async def test_basic_polymorphic_node(self):
        @scalar_node
        class IntSource:
            @classmethod
            def __compose__(cls) -> int:
                return 42

        @scalar_node
        @polymorphic[str]
        class StringConverter:
            @case
            def from_int(cls, value: IntSource) -> str:
                return f"Number: {value}"

        agent = EventLoopAgent.build({StringConverter})
        scope = Scope(detail="test")

        async with scope:
            await agent.run(local_scope=scope, mapped_scopes={})
            result = scope.retrieve(StringConverter)
            assert fntypes.is_some(result)
            assert result.unwrap().value == "Number: 42"

    @pytest.mark.asyncio
    async def test_multiple_cases_polymorphic(self):
        @scalar_node
        class StringSource:
            @classmethod
            def __compose__(cls) -> str:
                return "hello"

        @scalar_node
        @polymorphic[str]
        class MultiConverter:
            @case
            def from_string(cls, s: StringSource) -> str:
                return s.upper()

        # Test with string source
        agent = EventLoopAgent.build({MultiConverter, StringSource})
        scope = Scope(detail="test")

        async with scope:
            await agent.run(local_scope=scope, mapped_scopes={})
            result = scope.retrieve(MultiConverter)
            assert fntypes.is_some(result)
            # Should use the string case since StringSource is available
            assert result.unwrap().value == "HELLO"


class TestComplexPolymorphic:
    @pytest.mark.asyncio
    async def test_polymorphic_with_dependencies(self):
        @scalar_node
        class BaseValue:
            @classmethod
            def __compose__(cls) -> int:
                return 10

        @scalar_node
        class Multiplier:
            @classmethod
            def __compose__(cls) -> int:
                return 5

        @scalar_node
        @polymorphic[int]
        class Calculator:
            @case
            def multiply(cls, base: BaseValue, mult: Multiplier) -> int:
                return base * mult

        agent = EventLoopAgent.build({Calculator})
        scope = Scope(detail="test")

        async with scope:
            await agent.run(local_scope=scope, mapped_scopes={})
            result = scope.retrieve(Calculator)
            assert fntypes.is_some(result)
            assert result.unwrap().value == 50
