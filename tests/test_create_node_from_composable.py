import typing

import pytest

from nodnod.agent import EventLoopAgent
from nodnod.node import Node
from nodnod.scope import Scope
from nodnod.utils.create_node import create_node_from_composable


class TestCreateNodeFromComposable:
    def test_creates_node_from_simple_composable(self):
        class SimpleComposable:
            @classmethod
            def __compose__(cls) -> None: ...

        node_class = create_node_from_composable(SimpleComposable)

        assert issubclass(node_class, Node)
        assert node_class.__name__ == "Node:SimpleComposable"
        assert node_class.__type__ is SimpleComposable
        assert node_class.__compose__.__func__ is SimpleComposable.__compose__.__func__
        assert node_class.__module__ == SimpleComposable.__module__

    def test_creates_node_from_composable_with_dependencies(self):
        class DependencyComposable:
            @classmethod
            def __compose__(cls) -> None: ...

        class MainComposable:
            @classmethod
            def __compose__(cls, dep: DependencyComposable) -> None: ...

        node_class = create_node_from_composable(MainComposable)

        assert issubclass(node_class, Node)
        assert node_class.__name__ == "Node:MainComposable"
        assert node_class.__type__ is MainComposable
        assert node_class.__compose__.__func__ is MainComposable.__compose__.__func__

    def test_creates_node_from_async_composable(self):
        class AsyncComposable:
            @classmethod
            async def __compose__(cls) -> None: ...

        node_class = create_node_from_composable(AsyncComposable)

        assert issubclass(node_class, Node)
        assert node_class.__name__ == "Node:AsyncComposable"
        assert node_class.__type__ is AsyncComposable
        assert node_class.__compose__.__func__ is AsyncComposable.__compose__.__func__

    def test_creates_node_from_generator_composable(self):
        class GeneratorComposable:
            @classmethod
            def __compose__(cls) -> typing.Generator[int, None, None]:  # pragma: no cover
                yield 1
                yield 2
                yield 3

        node_class = create_node_from_composable(GeneratorComposable)

        assert issubclass(node_class, Node)
        assert node_class.__name__ == "Node:GeneratorComposable"
        assert node_class.__type__ is GeneratorComposable
        assert node_class.__compose__.__func__ is GeneratorComposable.__compose__.__func__

    def test_caching_behavior(self):
        class CachedComposable:
            @classmethod
            def __compose__(cls) -> None: ...

        node_class_1 = create_node_from_composable(CachedComposable)
        node_class_2 = create_node_from_composable(CachedComposable)
        assert node_class_1 is node_class_2

    def test_different_composables_create_different_nodes(self):
        class ComposableA:
            @classmethod
            def __compose__(cls) -> None: ...

        class ComposableB:
            @classmethod
            def __compose__(cls) -> None: ...

        node_class_a = create_node_from_composable(ComposableA)
        node_class_b = create_node_from_composable(ComposableB)

        assert node_class_a is not node_class_b
        assert node_class_a.__name__ == "Node:ComposableA"
        assert node_class_b.__name__ == "Node:ComposableB"
        assert node_class_a.__type__ is ComposableA
        assert node_class_b.__type__ is ComposableB

    def test_preserves_module_information(self):
        class ModuleComposable:
            __module__ = "test.module"

            @classmethod
            def __compose__(cls) -> None: ...

        node_class = create_node_from_composable(ModuleComposable)

        assert node_class.__module__ == "test.module"

    def test_created_node_inherits_from_node(self):
        class InheritanceComposable:
            @classmethod
            def __compose__(cls) -> None: ...

        node_class = create_node_from_composable(InheritanceComposable)

        assert issubclass(node_class, Node)
        assert Node in node_class.__mro__

    def test_name_format(self):
        class NameTestComposable:
            @classmethod
            def __compose__(cls) -> None: ...

        node_class = create_node_from_composable(NameTestComposable)

        assert node_class.__name__ == "Node:NameTestComposable"

    def test_composable_with_complex_signature(self):
        class ComplexComposable:
            @classmethod
            def __compose__(
                cls,
                required_param: str,
                optional_param: int = 42,
                *args: typing.Any,
                keyword_param: bool = False,
                **kwargs: typing.Any,
            ) -> None: ...

        node_class = create_node_from_composable(ComplexComposable)

        assert issubclass(node_class, Node)
        assert node_class.__compose__.__func__ is ComplexComposable.__compose__.__func__

    def test_composable_with_generic_return_type(self):
        class GenericComposable:
            @classmethod
            def __compose__(cls) -> None: ...

        node_class = create_node_from_composable(GenericComposable)

        assert issubclass(node_class, Node)
        assert node_class.__type__ is GenericComposable

    def test_node_class_has_correct_attributes(self):

        class AttributeComposable:
            custom_attr = "custom_value"

            @classmethod
            def __compose__(cls) -> None: ...

        node_class = create_node_from_composable(AttributeComposable)

        assert hasattr(node_class, "__type__")
        assert hasattr(node_class, "__compose__")
        assert hasattr(node_class, "__module__")

        assert node_class.__type__ is AttributeComposable
        assert node_class.__compose__.__func__ is AttributeComposable.__compose__.__func__
        assert node_class.__module__ == AttributeComposable.__module__

    def test_cache_key_uniqueness(self):
        def create_composable_a():
            class SameName:
                @classmethod
                def __compose__(cls) -> None: ...

            return SameName

        def create_composable_b():
            class SameName:
                @classmethod
                def __compose__(cls) -> None: ...

            return SameName

        composable_a = create_composable_a()
        composable_b = create_composable_b()

        node_class_a = create_node_from_composable(composable_a)
        node_class_b = create_node_from_composable(composable_b)

        assert node_class_a is not node_class_b
        assert node_class_a.__type__ is composable_a
        assert node_class_b.__type__ is composable_b

    def test_composable_without_return_annotation(self):
        class NoAnnotationComposable:
            @classmethod
            def __compose__(cls) -> None: ...

        node_class = create_node_from_composable(NoAnnotationComposable)

        assert issubclass(node_class, Node)
        assert node_class.__name__ == "Node:NoAnnotationComposable"
        assert node_class.__type__ is NoAnnotationComposable

    def test_composable_with_class_variables(self):
        class ComposableWithVars:
            class_var = "class_value"

            @classmethod
            def __compose__(cls) -> None: ...

        node_class = create_node_from_composable(ComposableWithVars)

        assert issubclass(node_class, Node)
        assert node_class.__type__ is ComposableWithVars
        assert hasattr(node_class, "class_var")

    def test_composable_with_staticmethod(self):
        class ComposableWithStatic:
            @staticmethod
            def helper_method() -> str:
                return "helper"

            @classmethod
            def __compose__(cls) -> None: ...

        node_class = create_node_from_composable(ComposableWithStatic)

        assert issubclass(node_class, Node)
        assert node_class.__type__ is ComposableWithStatic
        assert ComposableWithStatic.helper_method() == "helper"

    def test_composable_with_inheritance(self):
        class BaseComposable:
            base_value = "base"

            @classmethod
            def base_method(cls) -> None: ...

        class DerivedComposable(BaseComposable):
            @classmethod
            def __compose__(cls) -> None: ...

        node_class = create_node_from_composable(DerivedComposable)

        assert issubclass(node_class, Node)
        assert node_class.__type__ is DerivedComposable
        assert node_class.__name__ == "Node:DerivedComposable"

    def test_cache_invalidation_not_possible(self):
        class CacheTestComposable:
            @classmethod
            def __compose__(cls) -> None: ...

        node_class_1 = create_node_from_composable(CacheTestComposable)
        node_class_2 = create_node_from_composable(CacheTestComposable)

        CacheTestComposable.new_attr = "added_later"  # type: ignore
        node_class_3 = create_node_from_composable(CacheTestComposable)

        assert node_class_1 is node_class_2 is node_class_3

        assert node_class_1.__type__ is CacheTestComposable
        assert hasattr(CacheTestComposable, "new_attr")

    def test_node_initialization_attributes(self):
        class InitTestComposable:
            @classmethod
            def __compose__(cls) -> None: ...

        node_class = create_node_from_composable(InitTestComposable)

        assert hasattr(node_class, "__dependencies__")
        assert hasattr(node_class, "__injections__")
        assert hasattr(node_class, "__initialize__")
        assert hasattr(node_class, "__traverse__")

        assert isinstance(node_class.__dependencies__, set)
        assert isinstance(node_class.__injections__, set)

    def test_composable_node_with_generic(self):
        class GenericComposable[T]:
            @classmethod
            def __compose__(cls) -> None: ...

        node_class1 = create_node_from_composable(GenericComposable[str])
        node_class2 = create_node_from_composable(GenericComposable[int])
        assert node_class1 is node_class2

    @pytest.mark.asyncio
    async def test_create_node_from_async_composable(self):
        class AsyncComposable:
            @classmethod
            async def __compose__(cls) -> None: ...

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
