import pytest

from nodnod import Annotate, Node


def test_annotate_basic():
    class MyNode(Node):
        def __compose__(self) -> int:
            ...

    annotate = Annotate[int, MyNode]
    assert isinstance(annotate, Annotate)  # type: ignore
    assert annotate.annotation is int  # type: ignore[attr-defined]
    assert annotate.composable is MyNode  # type: ignore[attr-defined]


def test_annotate_with_one_argument():
    with pytest.raises(TypeError, match=r"^Expected 2 items \(annotation and composable like\), got `<class 'int'>`"):
        Annotate[int]


def test_annotate_second_argument_must_be_composable():
    with pytest.raises(TypeError, match=r"^Second argument of `Annotate` must be a `Composable`, got `<class 'int'>`"):
        Annotate[int, int]
