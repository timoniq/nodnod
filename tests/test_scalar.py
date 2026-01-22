import pytest

from nodnod import Scalar, Node


def test_scalar_basic():
    class MyNode(Node):
        def __compose__(self) -> int:
            ...

    annotate = Scalar[int, MyNode]
    assert isinstance(annotate, Scalar)  # type: ignore
    assert annotate.annotation is int  # type: ignore[attr-defined]
    assert annotate.composable is MyNode  # type: ignore[attr-defined]


def test_scalar_with_one_argument():
    with pytest.raises(TypeError, match=r"^Expected 2 items \(annotation and composable like\), got `<class 'int'>`"):
        Scalar[int]


def test_scalar_second_argument_must_be_composable():
    with pytest.raises(TypeError, match=r"^Second argument of `Scalar` must be a `Composable`, got `<class 'int'>`"):
        Scalar[int, int]
