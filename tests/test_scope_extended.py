import asyncio

import pytest

from nodnod import Scope, Value
from nodnod.error import NodeError
from nodnod.scope import validate_local_scope_is_linked_to_node_scopes


class TestScopeExtended:
    def test_scope_context_manager_sync(self):
        scope = Scope(detail="sync_test")

        with scope:
            assert not scope.is_closed

        assert scope.is_closed

    @pytest.mark.asyncio
    async def test_scope_context_manager_exception_handling(self):
        scope = Scope(detail="exception_test")

        try:
            async with scope:
                raise ValueError("Test exception")
        except ValueError:
            pass

        assert scope.is_closed

    def test_scope_merge(self):
        parent = Scope(detail="parent")
        child = parent.create_child("child")
        grandchild = child.create_child("grandchild")

        # Add values at different levels
        parent.push(Value(str, "parent_value"))
        child.push(Value(int, 42))
        grandchild.push(Value(float, 3.14))

        merged = grandchild.merge()

        assert merged.retrieve(str).unwrap().value == "parent_value"
        assert merged.retrieve(int).unwrap().value == 42
        assert merged.retrieve(float).unwrap().value == 3.14

    def test_scope_close_already_closed(self):
        scope = Scope(detail="test")
        scope.close()

        with pytest.raises(RuntimeError, match="already been closed"):
            scope.close()

    def test_validate_local_scope_is_linked_to_node_scopes_valid(self):
        from nodnod import Node

        class TestNode(Node):
            pass

        parent = Scope(detail="parent")
        child = parent.create_child("child")

        # This should not raise
        validate_local_scope_is_linked_to_node_scopes(child, {TestNode: parent})

    def test_validate_local_scope_is_linked_to_node_scopes_invalid(self):
        from nodnod import Node

        class TestNode(Node):
            pass

        scope1 = Scope(detail="scope1")
        scope2 = Scope(detail="scope2")

        with pytest.raises(NodeError):
            validate_local_scope_is_linked_to_node_scopes(scope1, {TestNode: scope2})

    @pytest.mark.asyncio
    async def test_scope_close_with_async_values(self):
        class AsyncClosable:
            def __init__(self):
                self.closed = False

            async def close(self):
                self.closed = True

        obj = AsyncClosable()

        async def gen():
            yield obj
            await obj.close()

        generator = gen()
        await generator.__anext__()

        scope = Scope(detail="async_test")
        scope.push(Value(AsyncClosable, obj, generator=generator))

        await scope.close()
        # Note: The actual close behavior depends on Value implementation
        assert obj.closed
        assert scope.is_closed
