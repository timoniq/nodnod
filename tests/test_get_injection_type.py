import pytest
from typing_extensions import ForwardRef

from nodnod import Injection
from nodnod.utils.injection import get_injection_type


class TestGetInjectionType:
    def test_get_injection_type_error_on_no_args(self):
        with pytest.raises(ValueError, match="Injection must have exactly one type argument."):
            get_injection_type(Injection)

    def test_get_injection_type_with_str_forward_ref(self):
        assert get_injection_type(Injection["int"]) == int

    def test_get_injection_type_with_forward_ref(self):
        t = get_injection_type(Injection[ForwardRef("int")])
        assert t is int

    def test_get_injection_type_with_unresolvable_str_forward_ref(self):
        t = get_injection_type(Injection["UnknownType"])
        assert isinstance(t, ForwardRef)
        assert t.__forward_arg__ == "UnknownType"

    def test_get_injection_type_with_injection(self):
        assert get_injection_type(Injection[str]) == str
