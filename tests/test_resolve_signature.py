import pytest
import typing
from nodnod.utils.resolve_signature import resolve_signature, Signature


class TestResolveSignature:
    def test_resolve_signature_simple_function(self):
        def simple_func(a: int, b: str) -> None:
            pass
        
        sig = resolve_signature(simple_func)
        assert isinstance(sig, Signature)
        assert 'a' in sig.args
        assert 'b' in sig.args
        assert sig.args['a'] == int
        assert sig.args['b'] == str
    
    def test_resolve_signature_with_defaults(self):
        def func_with_defaults(a: int, b: str = "default") -> None:
            pass
        
        sig = resolve_signature(func_with_defaults)
        assert 'a' in sig.args
        assert 'b' in sig.kwargs
        assert sig.kwargs['b'] == str
    
    def test_resolve_signature_ignore_bound_parameters(self):
        class TestClass:
            def method(self, a: int, b: str) -> None:
                pass
        
        sig = resolve_signature(TestClass.method, ignore_bound_parameters=True)
        # Should ignore 'self'
        assert 'a' in sig.args
        assert 'b' in sig.args
        assert len(sig.args) == 2
    
    def test_resolve_signature_class_method(self):
        class TestClass:
            @classmethod
            def class_method(cls, a: int, b: str) -> None:
                pass
        
        sig = resolve_signature(TestClass.class_method, ignore_bound_parameters=True)
        # Should ignore 'cls'
        assert 'a' in sig.args
        assert 'b' in sig.args
    
    def test_signature_get_all_types(self):
        def func(a: int, b: str, c: bool = True) -> None:
            pass
        
        sig = resolve_signature(func)
        all_types = sig.get_all_types()
        
        assert int in all_types
        assert str in all_types
        assert bool in all_types
    
    def test_resolve_signature_staticmethod(self):
        class TestClass:
            @staticmethod
            def static_method(a: int, b: str) -> None:
                pass
        
        sig = resolve_signature(TestClass.static_method)
        assert 'a' in sig.args
        assert 'b' in sig.args
    
    def test_resolve_signature_framework_specific(self):
        from nodnod import scalar_node
        
        @scalar_node
        class TestNode:
            @classmethod
            def __compose__(cls, a: int, b: str) -> int:
                return a
        
        # Test that framework can resolve signatures of node compositions
        sig = resolve_signature(TestNode.__compose__, ignore_bound_parameters=True)
        assert 'a' in sig.args
        assert 'b' in sig.args