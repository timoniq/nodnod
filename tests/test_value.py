from nodnod import Value
from nodnod.utils.aio import awaitable_noop


class TestValue:
    def test_value_creation(self):
        value = Value(int, 42)
        assert value.cls == int
        assert value.value == 42

    def test_value_unbox(self):
        value = Value(str, "hello")
        unboxed = value.unbox()
        assert unboxed == "hello"

    def test_value_close_no_generator(self):
        value = Value(int, 42, generator=None)
        result = value.close()
        assert isinstance(result, awaitable_noop)

    def test_value_repr(self):
        value = Value(int, 42)
        repr_str = repr(value)
        assert "int" in repr_str
        assert "42" in repr_str
