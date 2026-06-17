import typing

import pytest

from nodnod.error import NodeBuildError
from nodnod.utils.type_args import get_type_args_values


def test_get_type_args_values_empty_parameters():
    result = get_type_args_values(args=(int, str), parameters=())
    assert result == {}


def test_get_type_args_values_no_args():
    T = typing.TypeVar("T")
    U = typing.TypeVar("U")
    # No type arguments and no PEP 696 defaults -> fail loudly rather than storing NoDefault.
    with pytest.raises(NodeBuildError, match="Missing type argument for `T`"):
        get_type_args_values(args=(), parameters=(T, U))


def test_get_type_args_values_no_args_with_defaults():
    T = typing.TypeVar("T", default=int)
    U = typing.TypeVar("U", default=str)
    result = get_type_args_values(args=(), parameters=(T, U))
    assert result == {T: int, U: str}


def test_get_type_args_values_basic_typevar():
    T = typing.TypeVar("T")
    U = typing.TypeVar("U")
    result = get_type_args_values(args=(int, str), parameters=(T, U))
    assert result == {T: int, U: str}


def test_get_type_args_values_partial_args():
    T = typing.TypeVar("T")
    U = typing.TypeVar("U")
    V = typing.TypeVar("V")
    # V has neither a supplied argument nor a default -> NodeBuildError.
    with pytest.raises(NodeBuildError, match="Missing type argument for `V`"):
        get_type_args_values(args=(int, str), parameters=(T, U, V))


def test_get_type_args_values_partial_args_with_default():
    T = typing.TypeVar("T")
    U = typing.TypeVar("U")
    V = typing.TypeVar("V", default=float)
    result = get_type_args_values(args=(int, str), parameters=(T, U, V))
    assert result == {T: int, U: str, V: float}


def test_get_type_args_values_with_typevar_tuple():
    T = typing.TypeVar("T")
    Ts = typing.TypeVarTuple("Ts")
    U = typing.TypeVar("U")

    result = get_type_args_values(args=(int, str, float, bool), parameters=(T, Ts, U))
    assert result[T] == int
    assert result[U] == bool


def test_get_type_args_values_typevar_tuple_minimal():
    T = typing.TypeVar("T")
    Ts = typing.TypeVarTuple("Ts")
    U = typing.TypeVar("U")

    result = get_type_args_values(args=(int, str), parameters=(T, Ts, U))
    # T=int, Ts не получает ничего, U=str
    assert result[T] == int
    assert result[U] == str


def test_get_type_args_values_typevar_tuple_no_space():
    Ts = typing.TypeVarTuple("Ts")
    T = typing.TypeVar("T")

    result = get_type_args_values(args=(int,), parameters=(Ts, T))
    assert result[T] == int


def test_get_type_args_values_multiple_typevar_tuples():
    Ts1 = typing.TypeVarTuple("Ts1")
    Ts2 = typing.TypeVarTuple("Ts2")
    T = typing.TypeVar("T")

    result = get_type_args_values(args=(int, str, float), parameters=(Ts1, Ts2, T))
    assert result[T] == float


def test_get_type_args_values_excess_args():
    T = typing.TypeVar("T")
    result = get_type_args_values(args=(int, str, float), parameters=(T,))
    assert result == {T: int}


def test_get_type_args_values_with_param_spec():
    P = typing.ParamSpec("P")
    T = typing.TypeVar("T")

    result = get_type_args_values(args=(int, str), parameters=(P, T))
    assert result[P] == int
    assert result[T] == str
