import asyncio
from typing import Any

import kungfu
import pytest

from nodnod.agent.event_loop.coroutine import (
    compose_coroutine,
    dependency_concurrent_either_coroutine,
    dependency_sequential_either_coroutine,
    result_node_compose_coroutine,
)
from nodnod.error import NodeError
from nodnod.interface.result_node import ResultNode
from nodnod.node import Node
from nodnod.scope import Scope
from nodnod.value import Value


class TestNode(Node):
    __type__ = int

    @classmethod
    def __compose__(cls):
        return 42


class ErrorNode(Node):
    __type__ = str

    @classmethod
    def __compose__(cls):
        raise ValueError("Test error")  # pragma: no cover


class TestResultNode(ResultNode):
    __from_node__ = TestNode
    __error__ = ValueError
    __type__ = str


class NonHandlingResultNode(ResultNode):
    __from_node__ = ErrorNode
    __error__ = TypeError
    __type__ = str


@pytest.mark.asyncio
async def test_compose_coroutine_success():
    node_scope = Scope()
    local_scope = Scope()

    successful_future = asyncio.Future()
    successful_future.set_result(kungfu.Ok(Value(int, 42)))

    result = await compose_coroutine(TestNode, node_scope, local_scope, [successful_future])

    assert kungfu.is_ok(result)


@pytest.mark.asyncio
async def test_compose_coroutine_dependency_error():
    node_scope = Scope()
    local_scope = Scope()

    error_future = asyncio.Future()
    error_future.set_result(kungfu.Error(NodeError("dependency error")))

    result = await compose_coroutine(TestNode, node_scope, local_scope, [error_future])

    assert kungfu.is_err(result)
    assert "could not resolve dependencies" in str(result.error)


@pytest.mark.asyncio
async def test_result_node_compose_coroutine_exception():
    node_scope = Scope()

    exception_future = asyncio.Future()
    exception_future.set_exception(ValueError("Test exception"))

    result = await result_node_compose_coroutine(TestResultNode, node_scope, exception_future)

    assert kungfu.is_ok(result)
    assert TestResultNode in node_scope


@pytest.mark.asyncio
async def test_result_node_compose_coroutine_exception_not_handled():
    node_scope = Scope()

    exception_future = asyncio.Future()
    exception_future.set_exception(ValueError("Test exception"))

    with pytest.raises(ValueError):
        await result_node_compose_coroutine(NonHandlingResultNode, node_scope, exception_future)


@pytest.mark.asyncio
async def test_result_node_compose_coroutine_error_result():
    node_scope = Scope()

    error_future = asyncio.Future()
    error_future.set_result(kungfu.Error(NodeError("test error")))

    class ValueErrorHandlingResultNode(ResultNode):
        __from_node__ = TestNode
        __error__ = NodeError
        __type__ = str

    result = await result_node_compose_coroutine(ValueErrorHandlingResultNode, node_scope, error_future)

    assert kungfu.is_ok(result)
    assert ValueErrorHandlingResultNode in node_scope


@pytest.mark.asyncio
async def test_result_node_compose_coroutine_error_not_handled():
    node_scope = Scope()

    error_future = asyncio.Future()
    error_future.set_result(kungfu.Error(NodeError("test error")))

    with pytest.raises(NodeError):
        await result_node_compose_coroutine(NonHandlingResultNode, node_scope, error_future)


@pytest.mark.asyncio
async def test_dependency_sequential_either_coroutine_first_success():
    first_future = asyncio.Future()
    first_future.set_result(kungfu.Ok(Value(int, 42)))

    first_dependency = (TestNode, first_future)
    other_dependencies = ()
    futures = {}
    pusher = lambda f, n: None
    mapped_scopes = {}
    local_scope = Scope()

    result = await dependency_sequential_either_coroutine(
        first_dependency, other_dependencies, futures, pusher, mapped_scopes, local_scope
    )

    assert kungfu.is_ok(result)


@pytest.mark.asyncio
async def test_dependency_sequential_either_coroutine_existing_future():
    first_future = asyncio.Future()
    first_future.set_result(kungfu.Error(NodeError("first failed")))

    second_future = asyncio.Future()
    second_future.set_result(kungfu.Ok(Value(str, "success")))

    first_dependency = (TestNode, first_future)
    other_dependencies = (ErrorNode,)
    futures = {ErrorNode: second_future}
    pusher = lambda f, n: None
    mapped_scopes = {}
    local_scope = Scope()

    result = await dependency_sequential_either_coroutine(
        first_dependency, other_dependencies, futures, pusher, mapped_scopes, local_scope
    )

    assert kungfu.is_ok(result)


@pytest.mark.asyncio
async def test_dependency_sequential_either_coroutine_all_fail():
    first_future = asyncio.Future()
    first_future.set_result(kungfu.Error(NodeError("first failed")))

    first_dependency = (TestNode, first_future)
    other_dependencies = (ErrorNode,)
    futures: dict[Any, Any] = {}

    def mock_pusher(f, n):
        new_future = asyncio.Future()
        new_future.set_result(kungfu.Error(NodeError("pushed failed")))
        f[n] = new_future

    mapped_scopes = {}
    local_scope = Scope()

    result = await dependency_sequential_either_coroutine(
        first_dependency, other_dependencies, futures, mock_pusher, mapped_scopes, local_scope
    )

    assert kungfu.is_err(result)
    assert "no option found for either" in str(result.error)


@pytest.mark.asyncio
async def test_dependency_concurrent_either_coroutine_success():
    success_future = asyncio.Future()
    success_future.set_result(kungfu.Ok(Value(int, 42)))

    result = await dependency_concurrent_either_coroutine([success_future])

    assert kungfu.is_ok(result)


@pytest.mark.asyncio
async def test_dependency_concurrent_either_coroutine_all_fail():
    fail_future1 = asyncio.Future()
    fail_future1.set_result(kungfu.Error(NodeError("failed 1")))

    fail_future2 = asyncio.Future()
    fail_future2.set_result(kungfu.Error(NodeError("failed 2")))

    result = await dependency_concurrent_either_coroutine([fail_future1, fail_future2])

    assert kungfu.is_err(result)
    assert "no option found for either" in str(result.error)


@pytest.mark.asyncio
async def test_result_node_compose_coroutine_error_handled():
    node_scope = Scope()

    error_future = asyncio.Future()
    error_future.set_result(kungfu.Error(ValueError("test error")))

    class ValueErrorHandlingResultNode(ResultNode):
        __from_node__ = TestNode
        __error__ = ValueError
        __type__ = str

    result = await result_node_compose_coroutine(ValueErrorHandlingResultNode, node_scope, error_future)

    assert kungfu.is_ok(result)
    assert ValueErrorHandlingResultNode in node_scope
    value = node_scope[ValueErrorHandlingResultNode]
    assert kungfu.is_err(value.value)


@pytest.mark.asyncio
async def test_dependency_sequential_either_coroutine_existing_future_fails():
    first_future = asyncio.Future()
    first_future.set_result(kungfu.Error(NodeError("first failed")))

    existing_fail_future = asyncio.Future()
    existing_fail_future.set_result(kungfu.Error(NodeError("existing failed")))

    first_dependency = (TestNode, first_future)
    other_dependencies = (ErrorNode,)
    futures = {ErrorNode: existing_fail_future}
    pusher = lambda f, n: None
    mapped_scopes = {}
    local_scope = Scope()

    result = await dependency_sequential_either_coroutine(
        first_dependency, other_dependencies, futures, pusher, mapped_scopes, local_scope
    )

    assert kungfu.is_err(result)
    assert "no option found for either" in str(result.error)
