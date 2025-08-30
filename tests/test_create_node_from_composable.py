import typing

import pytest

from nodnod.agent import EventLoopAgent
from nodnod.node import Node
from nodnod.scope import Scope
from nodnod.utils.create_node import create_node_from_composable


class TestCreateNodeFromComposable:
    """Tests for create_node_from_composable function."""
    
    def test_creates_node_from_simple_composable(self):
        """Test that create_node_from_composable creates a valid Node subclass from a Composable."""
        
        class SimpleComposable:
            @classmethod
            def __compose__(cls) -> int:
                return 42
        
        # Act
        node_class = create_node_from_composable(SimpleComposable)
        
        # Assert
        assert issubclass(node_class, Node)
        assert node_class.__name__ == "Node:SimpleComposable"
        assert node_class.__type__ is SimpleComposable
        assert node_class.__compose__.__func__ is SimpleComposable.__compose__.__func__
        assert node_class.__module__ == SimpleComposable.__module__
    
    def test_creates_node_from_composable_with_dependencies(self):
        """Test creating a node from a composable that has dependencies."""
        
        class DependencyComposable:
            @classmethod
            def __compose__(cls) -> str:
                return "dependency"
        
        class MainComposable:
            @classmethod
            def __compose__(cls, dep: DependencyComposable) -> str:
                return f"main-{dep}"
        
        # Act
        node_class = create_node_from_composable(MainComposable)
        
        # Assert
        assert issubclass(node_class, Node)
        assert node_class.__name__ == "Node:MainComposable"
        assert node_class.__type__ is MainComposable
        assert node_class.__compose__.__func__ is MainComposable.__compose__.__func__
    
    def test_creates_node_from_async_composable(self):
        """Test creating a node from a composable with async __compose__."""
        
        class AsyncComposable:
            @classmethod
            async def __compose__(cls) -> str:
                return "async_result"
        
        # Act
        node_class = create_node_from_composable(AsyncComposable)
        
        # Assert
        assert issubclass(node_class, Node)
        assert node_class.__name__ == "Node:AsyncComposable"
        assert node_class.__type__ is AsyncComposable
        assert node_class.__compose__.__func__ is AsyncComposable.__compose__.__func__
    
    def test_creates_node_from_generator_composable(self):
        """Test creating a node from a composable that returns a generator."""
        
        class GeneratorComposable:
            @classmethod
            def __compose__(cls) -> typing.Generator[int, None, None]:
                yield 1
                yield 2
                yield 3
        
        # Act
        node_class = create_node_from_composable(GeneratorComposable)
        
        # Assert
        assert issubclass(node_class, Node)
        assert node_class.__name__ == "Node:GeneratorComposable"
        assert node_class.__type__ is GeneratorComposable
        assert node_class.__compose__.__func__ is GeneratorComposable.__compose__.__func__
    
    def test_caching_behavior(self):
        """Test that the @cache decorator works correctly."""
        
        class CachedComposable:
            @classmethod
            def __compose__(cls) -> int:
                return 123
        
        # Act - call twice
        node_class_1 = create_node_from_composable(CachedComposable)
        node_class_2 = create_node_from_composable(CachedComposable)
        
        # Assert - should return the same object due to caching
        assert node_class_1 is node_class_2
    
    def test_different_composables_create_different_nodes(self):
        """Test that different composables create different node classes."""
        
        class ComposableA:
            @classmethod
            def __compose__(cls) -> int:
                return 1
        
        class ComposableB:
            @classmethod
            def __compose__(cls) -> int:
                return 2
        
        # Act
        node_class_a = create_node_from_composable(ComposableA)
        node_class_b = create_node_from_composable(ComposableB)
        
        # Assert
        assert node_class_a is not node_class_b
        assert node_class_a.__name__ == "Node:ComposableA"
        assert node_class_b.__name__ == "Node:ComposableB"
        assert node_class_a.__type__ is ComposableA
        assert node_class_b.__type__ is ComposableB
    
    def test_preserves_module_information(self):
        """Test that the created node preserves the module information of the original composable."""
        
        class ModuleComposable:
            __module__ = "test.module"
            
            @classmethod
            def __compose__(cls) -> str:
                return "test"
        
        # Act
        node_class = create_node_from_composable(ModuleComposable)
        
        # Assert
        assert node_class.__module__ == "test.module"
    
    def test_created_node_inherits_from_node(self):
        """Test that the created class properly inherits from Node."""
        
        class InheritanceComposable:
            @classmethod
            def __compose__(cls) -> bool:
                return True
        
        # Act
        node_class = create_node_from_composable(InheritanceComposable)
        
        # Assert
        assert issubclass(node_class, Node)
        assert Node in node_class.__mro__
    
    def test_name_format(self):
        """Test that the generated node name follows the expected format."""
        
        class NameTestComposable:
            @classmethod
            def __compose__(cls) -> str:
                return "name_test"
        
        # Act
        node_class = create_node_from_composable(NameTestComposable)
        
        # Assert
        assert node_class.__name__ == "Node:NameTestComposable"
    
    def test_composable_with_complex_signature(self):
        """Test creating a node from a composable with complex parameter signature."""
        
        class ComplexComposable:
            @classmethod
            def __compose__(
                cls, 
                required_param: str,
                optional_param: int = 42,
                *args: typing.Any,
                keyword_param: bool = False,
                **kwargs: typing.Any
            ) -> dict:
                return {
                    "required": required_param,
                    "optional": optional_param,
                    "args": args,
                    "keyword": keyword_param,
                    "kwargs": kwargs
                }
        
        # Act
        node_class = create_node_from_composable(ComplexComposable)
        
        # Assert
        assert issubclass(node_class, Node)
        assert node_class.__compose__.__func__ is ComplexComposable.__compose__.__func__
    
    def test_composable_with_generic_return_type(self):
        """Test creating a node from a composable with generic return type."""
        
        class GenericComposable:
            @classmethod
            def __compose__(cls) -> typing.List[str]:
                return ["item1", "item2"]
        
        # Act
        node_class = create_node_from_composable(GenericComposable)
        
        # Assert
        assert issubclass(node_class, Node)
        assert node_class.__type__ is GenericComposable
    
    def test_node_class_has_correct_attributes(self):
        """Test that the created node class has all the expected attributes."""
        
        class AttributeComposable:
            custom_attr = "custom_value"
            
            @classmethod
            def __compose__(cls) -> str:
                return "test"
        
        # Act
        node_class = create_node_from_composable(AttributeComposable)
        
        # Assert
        # Check required attributes are set
        assert hasattr(node_class, "__type__")
        assert hasattr(node_class, "__compose__")
        assert hasattr(node_class, "__module__")
        
        # Check they have correct values
        assert node_class.__type__ is AttributeComposable
        assert node_class.__compose__.__func__ is AttributeComposable.__compose__.__func__
        assert node_class.__module__ == AttributeComposable.__module__
    
    def test_cache_key_uniqueness(self):
        """Test that cache properly distinguishes between different composables with same name."""
        
        # Create two different composables with the same name in different scopes
        def create_composable_a():
            class SameName:
                @classmethod
                def __compose__(cls) -> int:
                    return 1
            return SameName
        
        def create_composable_b():
            class SameName:
                @classmethod
                def __compose__(cls) -> int:
                    return 2
            return SameName
        
        composable_a = create_composable_a()
        composable_b = create_composable_b()
        
        # Act
        node_class_a = create_node_from_composable(composable_a)
        node_class_b = create_node_from_composable(composable_b)
        
        # Assert - should be different despite same name
        assert node_class_a is not node_class_b
        assert node_class_a.__type__ is composable_a
        assert node_class_b.__type__ is composable_b
    
    def test_composable_without_return_annotation(self):
        """Test creating a node from a composable without return type annotation."""
        
        class NoAnnotationComposable:
            @classmethod
            def __compose__(cls):
                return "no_annotation"
        
        # Act
        node_class = create_node_from_composable(NoAnnotationComposable)
        
        # Assert
        assert issubclass(node_class, Node)
        assert node_class.__name__ == "Node:NoAnnotationComposable"
        assert node_class.__type__ is NoAnnotationComposable
    
    def test_composable_with_class_variables(self):
        """Test creating a node from a composable with class variables."""
        
        class ComposableWithVars:
            class_var = "class_value"
            _private_var = "private"
            
            @classmethod
            def __compose__(cls) -> str:
                return cls.class_var
        
        # Act
        node_class = create_node_from_composable(ComposableWithVars)
        
        # Assert
        assert issubclass(node_class, Node)
        assert node_class.__type__ is ComposableWithVars
        # The created node should reference the original composable, not inherit its variables
        assert not hasattr(node_class, "class_var")
        assert ComposableWithVars.class_var == "class_value"
    
    def test_composable_with_staticmethod(self):
        """Test creating a node from a composable that has static methods."""
        
        class ComposableWithStatic:
            @staticmethod
            def helper_method():
                return "helper"
            
            @classmethod
            def __compose__(cls) -> str:
                return f"main_{cls.helper_method()}"
        
        # Act
        node_class = create_node_from_composable(ComposableWithStatic)
        
        # Assert
        assert issubclass(node_class, Node)
        assert node_class.__type__ is ComposableWithStatic
        # The static method should be accessible through the original class
        assert ComposableWithStatic.helper_method() == "helper"
    
    def test_composable_with_inheritance(self):
        """Test creating a node from a composable that inherits from another class."""
        
        class BaseComposable:
            base_value = "base"
            
            @classmethod
            def base_method(cls):
                return cls.base_value
        
        class DerivedComposable(BaseComposable):
            @classmethod
            def __compose__(cls) -> str:
                return f"derived_{cls.base_method()}"
        
        # Act
        node_class = create_node_from_composable(DerivedComposable)
        
        # Assert
        assert issubclass(node_class, Node)
        assert node_class.__type__ is DerivedComposable
        assert node_class.__name__ == "Node:DerivedComposable"
    
    def test_cache_invalidation_not_possible(self):
        """Test that the cache cannot be easily invalidated (demonstrating the @cache decorator)."""
        
        class CacheTestComposable:
            @classmethod
            def __compose__(cls) -> int:
                return 999
        
        # Act - create node multiple times
        node_class_1 = create_node_from_composable(CacheTestComposable)
        node_class_2 = create_node_from_composable(CacheTestComposable)
        
        # Modify the original composable (this won't affect cached result)
        CacheTestComposable.new_attr = "added_later"  # type: ignore
        node_class_3 = create_node_from_composable(CacheTestComposable)
        
        # Assert - all references should be the same object due to caching
        assert node_class_1 is node_class_2 is node_class_3
        
        # The cached node should still reference the original class
        assert node_class_1.__type__ is CacheTestComposable
        assert hasattr(CacheTestComposable, "new_attr")
    
    def test_node_initialization_attributes(self):
        """Test that the created node has the expected initialization attributes."""
        
        class InitTestComposable:
            @classmethod
            def __compose__(cls) -> float:
                return 3.14
        
        # Act
        node_class = create_node_from_composable(InitTestComposable)
        
        # Assert - check that Node initialization added required attributes
        assert hasattr(node_class, "__dependencies__")
        assert hasattr(node_class, "__injections__")
        assert hasattr(node_class, "__initialize__")
        assert hasattr(node_class, "__traverse__")
        
        # These should be set by Node.__init_subclass__
        assert isinstance(node_class.__dependencies__, set)
        assert isinstance(node_class.__injections__, set)

    @pytest.mark.asyncio
    async def test_create_node_from_async_composable(self):
        class AsyncComposable:
            @classmethod
            async def __compose__(cls) -> int:
                return 42
        
        node_class = create_node_from_composable(AsyncComposable)
        assert issubclass(node_class, Node)

    @pytest.mark.asyncio
    async def test_build_nodes_with_composable_dependencies(self):
        class ComposableDependency:
            @classmethod
            def __compose__(cls) -> int:
                return 42

        class NodeWithComposableDependency(Node):
            @classmethod
            def __compose__(cls, dep: ComposableDependency) -> int:
                assert dep == 42
                return 123

        global_scope = Scope(detail="global")
        local_scope = global_scope.create_child(detail="local")
        agent = EventLoopAgent.build(nodes={NodeWithComposableDependency})

        async with local_scope:
            await agent.run(local_scope=local_scope, mapped_scopes={})

        await global_scope.close()
