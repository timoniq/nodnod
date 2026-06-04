import pytest
from kungfu import UnwrapError

from nodnod.utils.call import call_with_context


def test_call_with_context():
    def func(a: int, b: str, c: bool = False):
        return a, b, c

    result = call_with_context(func, {"a": 1, "b": "2", "c": True}).unwrap()
    assert result == (1, "2", True)


def test_call_with_context_with_defaults():
    def func(a: int, b: str, c: bool = False):
        return a, b, c

    result = call_with_context(func, {"a": 1, "b": "2"}).unwrap()
    assert result == (1, "2", False)


def test_call_with_context_with_optional():
    def func(a: int, b: str, c: bool = False):
        return a, b, c

    result = call_with_context(func, {"a": 1, "b": "2", "c": True}).unwrap()
    assert result == (1, "2", True)


def test_call_with_context_with_optional_and_defaults():
    def func(a: int, b: str, c: bool = False):
        return a, b, c

    result = call_with_context(func, {"a": 1, "b": "2", "c": True}).unwrap()
    assert result == (1, "2", True)


def test_call_with_context_with_optional_and_defaults_and_positional_only():
    def func(a: int, /, b: str, c: bool = False):
        return a, b, c

    result = call_with_context(func, {"a": 1, "b": "2", "c": True}).unwrap()
    assert result == (1, "2", True)


def test_call_with_context_with_optional_and_defaults_and_positional_only_and_keyword_only():
    def func(a: int, /, b: str, c: bool = False):
        return a, b, c

    result = call_with_context(func, {"a": 1, "b": "2", "c": True}).unwrap()
    assert result == (1, "2", True)


def test_call_with_context_key_error():
    def func(a: int, /, b: str, c: bool = False): ...

    with pytest.raises(UnwrapError, match="b"):
        call_with_context(func, {"a": 1}).unwrap()
