import pytest

from nodnod.node import FORWARD_REF_REQUESTS, INITIALIZED_FORWARD_REFS


@pytest.fixture(autouse=True)
def _isolate_forward_ref_registries():
    """Snapshot and restore nodnod's module-level forward-ref registries around each test, so a
    test that defines nodes or parks forward refs cannot leak global state into another test."""
    saved_refs = dict(INITIALIZED_FORWARD_REFS)
    saved_requests = {name: list(reqs) for name, reqs in FORWARD_REF_REQUESTS.items()}
    try:
        yield
    finally:
        INITIALIZED_FORWARD_REFS.clear()
        INITIALIZED_FORWARD_REFS.update(saved_refs)
        FORWARD_REF_REQUESTS.clear()
        FORWARD_REF_REQUESTS.update(saved_requests)
