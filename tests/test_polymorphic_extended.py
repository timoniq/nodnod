import pytest
import asyncio
import fntypes
from nodnod import scalar_node, Node, Scope, EventLoopAgent
from nodnod.interface.polymorphic import polymorphic, case


class TestPolymorphicExtended:
    def test_case_decorator_with_regular_method(self):
        # Test case decorator on a regular method (not classmethod)
        def regular_method(cls, value: int) -> str:
            return f"value: {value}"
        
        decorated = case(regular_method)
        # Should convert to classmethod
        assert isinstance(decorated, classmethod)
    
    def test_case_decorator_with_classmethod(self):
        # Test case decorator on existing classmethod
        @classmethod
        def class_method(cls, value: int) -> str:
            return f"value: {value}"
        
        decorated = case(class_method)
        # Should remain classmethod
        assert isinstance(decorated, classmethod)
    
    @pytest.mark.asyncio
    async def test_polymorphic_non_scalar_return(self):
        @scalar_node
        class IntSource:
            @classmethod
            def __compose__(cls) -> int:
                return 42
        
        class NonScalarConverter(Node):
            # Remove is_scalar to make it non-scalar
            
            @case
            def from_int(cls, value: IntSource) -> str:
                return f"Number: {value}"
        
        # Apply polymorphic decorator
        PolyConverter = polymorphic[str](NonScalarConverter)
        
        agent = EventLoopAgent.build({PolyConverter})
        scope = Scope(detail="test")
        
        async with scope:
            await agent.run(local_scope=scope, mapped_scopes={})
            result = scope.retrieve(PolyConverter)
            assert fntypes.is_some(result)
            # Should return the node instance, not the scalar value
            node_instance = result.unwrap().value
            assert hasattr(node_instance, '__class__')