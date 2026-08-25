"""
Shared fixtures for memory integration tests.

Provides:
    - manager: a MemoryManager(provider="mem0") instance (session-scoped)
    - memory_id: the ID returned by an initial add_memory call
"""

import pytest


@pytest.fixture(scope="session")
def manager():
    """Create a MemoryManager with the mem0 provider."""
    from aios.memory.manager import MemoryManager

    mgr = MemoryManager(provider="mem0")
    yield mgr
    mgr.close()


@pytest.fixture(scope="session")
def memory_id(manager):
    """Add a seed memory and return its ID for downstream tests."""
    from cerebrum.memory.apis import MemoryQuery
    from aios.syscall.memory import MemorySyscall

    query = MemoryQuery(
        operation_type="add_memory",
        params={
            "content": "The Eiffel Tower is located in Paris, France.",
            "keywords": ["eiffel", "paris", "france"],
            "tags": ["geography", "landmarks"],
            "category": "Facts",
            "context": "World geography",
        },
    )
    syscall = MemorySyscall(agent_name="test_agent", query=query)
    resp = manager.address_request(syscall)
    return getattr(resp, "memory_id", None)
