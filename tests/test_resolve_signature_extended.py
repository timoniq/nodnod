import typing

from nodnod.utils.resolve_signature import resolve_signature


def test_signature_var_positional_type():
    def func_with_args(*args: int):
        ...

    signature = resolve_signature(func_with_args)
    assert signature.var_positional_type == int


def test_signature_var_positional_type_none():
    def func_without_args():
        ...

    signature = resolve_signature(func_without_args)
    assert signature.var_positional_type is None


def test_signature_var_keyword_type():
    def func_with_kwargs(**kwargs: str):
        ...

    signature = resolve_signature(func_with_kwargs)
    assert signature.var_keyword_type == str


def test_signature_var_keyword_type_none():
    def func_without_kwargs():
        ...

    signature = resolve_signature(func_without_kwargs)
    assert signature.var_keyword_type is None


def test_signature_get_all_types():
    def func_with_types(a: int, /, b: str = "default", *, c: bool = False):
        ...

    signature = resolve_signature(func_with_types)
    all_types = signature.get_all_types()

    assert int in all_types
    assert str in all_types
    assert bool in all_types
    assert len(all_types) == 3


def test_resolve_signature_with_staticmethod():
    class TestClass:
        @staticmethod
        def static_method(x: int) -> str:
            ...

    signature = resolve_signature(TestClass.__dict__["static_method"])

    assert "x" in signature.kwargs
    assert signature.kwargs["x"] == int


def test_resolve_signature_with_classmethod():
    class TestClass:
        @classmethod
        def class_method(cls, x: int) -> str:
            ...

    signature = resolve_signature(TestClass.__dict__["class_method"], ignore_bound_parameters=True)

    assert "cls" not in signature.kwargs
    assert "x" in signature.kwargs
    assert signature.kwargs["x"] == int


def test_resolve_signature_var_positional():
    def func_with_varargs(a: int, *args: str):
        ...

    signature = resolve_signature(func_with_varargs)

    assert signature.var_positional is not None
    assert signature.var_positional.annotation == str
    assert signature.var_positional_type == str


def test_resolve_signature_var_keyword():
    def func_with_varkwargs(a: int, **kwargs: float):
        ...

    signature = resolve_signature(func_with_varkwargs)

    assert signature.var_keyword is not None
    assert signature.var_keyword.annotation == float
    assert signature.var_keyword_type == float


def test_resolve_signature_string_annotation():
    def func_with_string_annotation(x: "int") -> str:
        ...

    signature = resolve_signature(func_with_string_annotation)

    assert "x" in signature.kwargs
    annotation = signature.kwargs["x"]
    assert annotation is int


def test_resolve_signature_positional_only():
    def func_with_posonly(a: int, /, b: str = "default"):
        ...

    signature = resolve_signature(func_with_posonly)

    assert "a" in signature.args
    assert signature.args["a"] == int

    assert "b" in signature.kwargs
    assert signature.kwargs["b"] == str


def test_signature_merge():
    def func_mixed(a: int, /, b: str = "default"):
        ...

    signature = resolve_signature(func_mixed)
    merged = signature.merge()

    assert "a" in merged
    assert "b" in merged
    assert merged["a"] == int
    assert merged["b"] == str


def test_resolve_signature_no_annotations():
    def func_no_annotations(x: typing.Any, y: typing.Any):
        ...

    signature = resolve_signature(func_no_annotations)

    assert "x" in signature.kwargs
    assert "y" in signature.kwargs
    assert signature.kwargs["x"] == typing.Any
    assert signature.kwargs["y"] == typing.Any
