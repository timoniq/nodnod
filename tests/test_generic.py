import typing

from nodnod.interface.composable import Composable
from nodnod.interface.generic import create_type_arg_node, generic_node, prepare_generic_node
from nodnod.node import Node


def test_prepare_generic_node_single_type():
    class _ComposableWithOneGeneric(Composable[typing.Any]):
        __type_params__ = (typing.TypeVar("T"),)

        def __compose__(self):
            pass  # pragma: no cover

    result = prepare_generic_node(_ComposableWithOneGeneric, int)

    assert issubclass(result, Node)
    assert result.__name__ == "_ComposableWithOneGeneric[int]"
    assert hasattr(result, "__type_args__")


def test_prepare_generic_node_tuple_types():
    class _ComposableWithMultiGeneric(Composable[typing.Any]):
        __type_params__ = (typing.TypeVar("T"), typing.TypeVar("U"))

        def __compose__(self):
            pass  # pragma: no cover

    result = prepare_generic_node(_ComposableWithMultiGeneric, (int, str))

    assert issubclass(result, Node)
    assert result.__name__ == "_ComposableWithMultiGeneric[int, str]"
    assert hasattr(result, "__type_args__")


def test_prepare_generic_node_caching():
    class _ComposableWithOneGeneric(Composable[typing.Any]):
        __type_params__ = (typing.TypeVar("T"),)

        def __compose__(self):
            pass  # pragma: no cover

    result1 = prepare_generic_node(_ComposableWithOneGeneric, int)
    result2 = prepare_generic_node(_ComposableWithOneGeneric, int)
    assert result1 is result2


def test_prepare_generic_node_different_types():
    class _ComposableWithOneGeneric(Composable[typing.Any]):
        __type_params__ = (typing.TypeVar("T"),)

        def __compose__(self):
            pass  # pragma: no cover

    result1 = prepare_generic_node(_ComposableWithOneGeneric, int)
    result2 = prepare_generic_node(_ComposableWithOneGeneric, str)

    assert result1 is not result2
    assert result1.__name__ == "_ComposableWithOneGeneric[int]"
    assert result2.__name__ == "_ComposableWithOneGeneric[str]"


def test_prepare_generic_node_sets_generics_attribute():
    class _ComposableWithOneGeneric(Composable[typing.Any]):
        __type_params__ = (typing.TypeVar("T"),)

        def __compose__(self):
            pass  # pragma: no cover

    result = prepare_generic_node(_ComposableWithOneGeneric, float)
    assert hasattr(_ComposableWithOneGeneric, "__generics__")
    assert (float,) in _ComposableWithOneGeneric.__generics__
    assert _ComposableWithOneGeneric.__generics__[(float,)] is result


def test_generic_node_creation():
    class _ComposableWithOneGeneric(Composable[typing.Any]):
        __type_params__ = (typing.TypeVar("T"),)

        def __compose__(self):
            pass  # pragma: no cover

    GenericTestNode = generic_node(_ComposableWithOneGeneric)

    assert GenericTestNode.__name__ == "_ComposableWithOneGeneric:?"
    assert GenericTestNode.__node_cls__ is _ComposableWithOneGeneric


def test_generic_node_class_getitem():
    class _ComposableWithOneGeneric(Composable[typing.Any]):
        __type_params__ = (typing.TypeVar("T"),)

        def __compose__(self):
            pass  # pragma: no cover

    GenericTestNode = generic_node(_ComposableWithOneGeneric)

    result = GenericTestNode[int]

    assert issubclass(result, Node)
    assert result.__name__ == "_ComposableWithOneGeneric[int]"


def test_create_type_arg_node():
    class _ComposableWithOneGeneric(Composable[typing.Any]):
        __type_params__ = (typing.TypeVar("T"),)

        def __compose__(self):
            pass  # pragma: no cover

    T = typing.TypeVar("T")
    generic_node_instance = prepare_generic_node(_ComposableWithOneGeneric, int)

    result = create_type_arg_node(generic_node_instance, T, int)

    assert issubclass(result, Node)
    assert result.__name__ == "TypeArgNode[T]"
    assert result.__type__ is int
    assert hasattr(result, "__compose__")


def test_create_type_arg_node_compose():
    class _ComposableWithOneGeneric(Composable[typing.Any]):
        __type_params__ = (typing.TypeVar("T"),)

        def __compose__(self):
            pass  # pragma: no cover

    T = typing.TypeVar("T")
    generic_node_instance = prepare_generic_node(_ComposableWithOneGeneric, int)

    generic_node_instance.__type_args__ = {T: int}

    type_arg_node = create_type_arg_node(generic_node_instance, T, int)

    compose_func = type_arg_node.__compose__
    result = compose_func()

    assert result is int


def test_prepare_generic_node_attributes():
    class _ComposableWithOneGeneric(Composable[typing.Any]):
        __type_params__ = (typing.TypeVar("T"),)

        def __compose__(self):
            pass  # pragma: no cover

    result = prepare_generic_node(_ComposableWithOneGeneric, str)

    assert result.__type__ is result
    assert hasattr(result, "__type_args__")
    assert hasattr(result, "__initialize__")
    assert hasattr(result, "__dependencies__")
    assert result.__module__ == _ComposableWithOneGeneric.__module__


def test_prepare_generic_node_inheritance():
    class _ComposableWithOneGeneric(Composable[typing.Any]):
        __type_params__ = (typing.TypeVar("T"),)

        def __compose__(self):
            pass  # pragma: no cover

    result = prepare_generic_node(_ComposableWithOneGeneric, bool)

    assert issubclass(result, Node)
    assert issubclass(result, _ComposableWithOneGeneric)


def test_multiple_generics_storage():
    class _ComposableWithOneGeneric(Composable[typing.Any]):
        __type_params__ = (typing.TypeVar("T"),)

        def __compose__(self):
            pass  # pragma: no cover

    node1 = prepare_generic_node(_ComposableWithOneGeneric, int)
    node2 = prepare_generic_node(_ComposableWithOneGeneric, str)
    node3 = prepare_generic_node(_ComposableWithOneGeneric, float)

    generics = getattr(_ComposableWithOneGeneric, "__generics__", {})

    assert len(generics) >= 3
    assert (int,) in generics
    assert (str,) in generics
    assert (float,) in generics
    assert generics[(int,)] is node1
    assert generics[(str,)] is node2
    assert generics[(float,)] is node3
