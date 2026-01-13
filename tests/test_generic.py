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

    assert GenericTestNode.__name__ == "_ComposableWithOneGeneric:[?]"
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


def test_prepare_generic_node_with_type_var_tuple_only():
    class _ComposableWithTypeVarTuple(Composable[typing.Any]):
        __type_params__ = (typing.TypeVarTuple("Ts"),)

        def __compose__(self):
            pass  # pragma: no cover

    result = prepare_generic_node(_ComposableWithTypeVarTuple, (int, str, float))

    assert issubclass(result, Node)
    assert result.__name__ == "_ComposableWithTypeVarTuple[int, str, float]"
    assert hasattr(result, "__type_args__")


def test_prepare_generic_node_with_type_var_tuple_empty():
    class _ComposableWithTypeVarTuple(Composable[typing.Any]):
        __type_params__ = (typing.TypeVarTuple("Ts"),)

        def __compose__(self):
            pass  # pragma: no cover

    result = prepare_generic_node(_ComposableWithTypeVarTuple, ())

    assert issubclass(result, Node)
    assert result.__name__ == "_ComposableWithTypeVarTuple[]"
    assert hasattr(result, "__type_args__")


def test_prepare_generic_node_with_type_var_and_type_var_tuple():
    class _ComposableWithMixed(Composable[typing.Any]):
        __type_params__ = (typing.TypeVar("T"), typing.TypeVarTuple("Ts"))

        def __compose__(self):
            pass  # pragma: no cover

    result = prepare_generic_node(_ComposableWithMixed, (int, str, float, bool))

    assert issubclass(result, Node)
    assert result.__name__ == "_ComposableWithMixed[int, str, float, bool]"
    assert hasattr(result, "__type_args__")


def test_prepare_generic_node_with_type_var_tuple_and_type_var():
    class _ComposableWithMixed(Composable[typing.Any]):
        __type_params__ = (typing.TypeVarTuple("Ts"), typing.TypeVar("U"))

        def __compose__(self):
            pass  # pragma: no cover

    result = prepare_generic_node(_ComposableWithMixed, (int, str, float, bool))

    assert issubclass(result, Node)
    assert result.__name__ == "_ComposableWithMixed[int, str, float, bool]"
    assert hasattr(result, "__type_args__")


def test_prepare_generic_node_with_type_var_tuple_between_type_vars():
    class _ComposableWithMixed(Composable[typing.Any]):
        __type_params__ = (typing.TypeVar("T"), typing.TypeVarTuple("Ts"), typing.TypeVar("U"))

        def __compose__(self):
            pass  # pragma: no cover

    result = prepare_generic_node(_ComposableWithMixed, (int, str, float, bool))

    assert issubclass(result, Node)
    assert result.__name__ == "_ComposableWithMixed[int, str, float, bool]"
    assert hasattr(result, "__type_args__")


def test_prepare_generic_node_type_var_tuple_type_args_values():
    class _ComposableWithTypeVarTuple(Composable[typing.Any]):
        Ts = typing.TypeVarTuple("Ts")
        __type_params__ = (Ts,)

        def __compose__(self):
            pass  # pragma: no cover

    result = prepare_generic_node(_ComposableWithTypeVarTuple, (int, str, float))

    assert hasattr(result, "__type_args__")
    assert _ComposableWithTypeVarTuple.Ts in result.__type_args__
    assert result.__type_args__[_ComposableWithTypeVarTuple.Ts] == (int, str, float)


def test_prepare_generic_node_mixed_type_args_values():
    class _ComposableWithMixed(Composable[typing.Any]):
        T = typing.TypeVar("T")
        Ts = typing.TypeVarTuple("Ts")
        U = typing.TypeVar("U")
        __type_params__ = (T, Ts, U)

        def __compose__(self):
            pass  # pragma: no cover

    result = prepare_generic_node(_ComposableWithMixed, (int, str, float, bool))

    assert hasattr(result, "__type_args__")
    assert _ComposableWithMixed.T in result.__type_args__
    assert _ComposableWithMixed.Ts in result.__type_args__
    assert _ComposableWithMixed.U in result.__type_args__
    assert result.__type_args__[_ComposableWithMixed.T] is int
    assert result.__type_args__[_ComposableWithMixed.Ts] == (str, float)
    assert result.__type_args__[_ComposableWithMixed.U] is bool
