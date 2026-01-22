from nodnod import Scope
from nodnod.value import Value


def test_scope_inject():
    scope = Scope()

    scope.inject(str, "test_value")

    assert str in scope
    value = scope[str]
    assert isinstance(value, Value)
    assert value.cls is str
    assert value.value == "test_value"


def test_scope_inject_different_types():
    scope = Scope()

    scope.inject(int, 42)
    scope.inject(float, 3.14)
    scope.inject(list, [1, 2, 3])

    assert scope[int].value == 42
    assert scope[float].value == 3.14
    assert scope[list].value == [1, 2, 3]


def test_scope_inject_overwrite():
    scope = Scope()

    scope.inject(str, "first")
    assert scope[str].value == "first"

    scope.inject(str, "second")
    assert scope[str].value == "second"
