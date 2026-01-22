import kungfu
import pytest

from nodnod import EventLoopAgent, Node, Scope, scalar_node
from nodnod.interface.polymorphic import case, polymorphic


class TestPolymorphicExtended:
    def test_case_decorator_with_regular_method(self):
        decorated = case(lambda cls: None)
        assert isinstance(decorated, classmethod)

    def test_case_decorator_with_classmethod(self):
        decorated = case(classmethod(lambda cls: None))
        assert isinstance(decorated, classmethod)

    @pytest.mark.asyncio
    async def test_polymorphic_non_scalar_return(self):
        @scalar_node
        class IntSource:
            @classmethod
            def __compose__(cls) -> int:
                return 42

        class NonScalarConverter(Node, abstract=True):
            @case
            def from_int(cls, value: IntSource) -> str:
                return f"Number: {value}"

        PolyConverter = polymorphic[str](NonScalarConverter)

        agent = EventLoopAgent.build({PolyConverter})
        scope = Scope(detail="test")

        async with scope:
            await agent.run(local_scope=scope, mapped_scopes={})
            result = scope.retrieve(PolyConverter)
            assert kungfu.is_some(result)
            # Should return the node instance, not the scalar value
            node_instance = result.unwrap().value
            assert hasattr(node_instance, "__class__")
