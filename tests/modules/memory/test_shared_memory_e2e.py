"""
End-to-end integration test: Cross-Agent Shared Memory Pipeline.

Validates the full write → retrieve → inject → format pipeline
against real Mem0 + ChromaDB + Ollama (nomic-embed-text embedder).

Flow:
  1. ProfileAgent writes a shared memory with user_id="e2e_test_user"
  2. TaskAgent writes a shared memory with the same user_id
  3. AssistantAgent's ContextInjector retrieves and injects both
  4. Asserts content is formatted to natural language (not raw JSON)
  5. Asserts diagnostics show both agents as sources

Prerequisites:
  - Ollama running locally (http://localhost:11434) with nomic-embed-text
  - Config patched for mem0 provider (scripts/patch_config_for_memory_tests.py)

Run:
    pytest tests/modules/memory/test_shared_memory_e2e.py -v -m integration
"""
import json
import os
import sys
import time
import uuid

import pytest
import urllib.request
import urllib.error

# Project root on sys.path
_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.abspath(os.path.join(_HERE, "..", "..", ".."))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

pytestmark = pytest.mark.integration

# Unique test user_id to avoid collisions with other test runs
TEST_USER_ID = f"e2e_test_{uuid.uuid4().hex[:8]}"


def _ollama_reachable() -> bool:
    """Check if Ollama is reachable at localhost:11434.

    Set OLLAMA_SKIP=1 to force unreachable (for testing the skip path).
    """
    if os.environ.get("OLLAMA_SKIP") == "1":
        return False
    try:
        req = urllib.request.Request(
            "http://localhost:11434/api/version",
            method="GET",
        )
        with urllib.request.urlopen(req, timeout=3):
            return True
    except (urllib.error.URLError, OSError):
        return False


def _wait_for_embedding(
    provider, user_id: str, expected_count: int,
    timeout: float = 30.0, poll_interval: float = 1.0,
) -> bool:
    """Poll until expected_count memories are retrievable.

    Mem0's add is async internally (embedding generation) so
    results may not be immediately retrievable. This poll avoids
    a fixed sleep.
    """
    from cerebrum.memory.apis import MemoryQuery

    deadline = time.time() + timeout
    while time.time() < deadline:
        query = MemoryQuery(
            operation_type="retrieve_memory",
            params={
                "content": "profile task context",
                "k": 10,
                "user_id": user_id,
            },
        )
        resp = provider.retrieve_memory(query)
        if resp.success and resp.search_results:
            if len(resp.search_results) >= expected_count:
                return True
        time.sleep(poll_interval)
    return False


class TestSharedMemoryE2E:
    """Full pipeline: write shared memories → inject into LLM context."""

    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        """Initialize MemoryManager with real mem0 config.

        Skips gracefully if Ollama is unreachable.
        Cleans up test memories on both success and failure.
        """
        if not _ollama_reachable():
            pytest.skip(
                "Ollama not reachable at localhost:11434 "
                "— skipping integration test"
            )

        from aios.config.config_manager import config
        from aios.hooks.modules.memory import useMemoryManager

        memory_config = config.get_memory_config()
        if memory_config.get("provider") != "mem0":
            pytest.skip(
                "Config not set to mem0 provider — run "
                "scripts/patch_config_for_memory_tests.py first"
            )

        self.memory_manager = useMemoryManager(
            log_mode="console",
        )
        self.memory_config = memory_config
        self._written_memory_ids = []

        yield

        # Cleanup: remove test memories
        for mid in self._written_memory_ids:
            try:
                self.memory_manager.provider.remove_memory(mid)
            except Exception:
                pass

    def _write_shared_memory(
        self, agent_name: str, content: str,
        memory_type: str,
    ) -> str:
        """Write a shared memory and track its ID for cleanup."""
        from aios.memory.note import MemoryNote

        note = MemoryNote(
            content=content,
            context=memory_type,
            category=memory_type,
        )
        note.metadata = {
            "user_id": TEST_USER_ID,
            "owner_agent": agent_name,
            "memory_type": memory_type,
            "sharing_policy": "shared",
        }

        result = self.memory_manager.provider.add_memory(note)
        if result.success and result.memory_id:
            self._written_memory_ids.append(result.memory_id)
        return result.memory_id or note.id

    def test_cross_agent_shared_memory_injection(self):
        """ProfileAgent + TaskAgent write shared → AssistantAgent
        retrieves both via ContextInjector with formatting."""
        from aios.memory.context_injector import ContextInjector
        from cerebrum.llm.apis import LLMQuery

        # --- Step 1: ProfileAgent writes shared profile memory ---
        profile_content = json.dumps({
            "name": "E2E Test User",
            "language": "Python",
            "tools": "pytest",
        })
        self._write_shared_memory(
            "profile_agent", profile_content, "profile",
        )

        # --- Step 2: TaskAgent writes shared task_context memory ---
        task_content = json.dumps({
            "project": "AIOS CI pipeline",
            "goals": "full integration coverage",
        })
        self._write_shared_memory(
            "task_agent", task_content, "task_context",
        )

        # --- Step 3: Wait for embeddings to be queryable ---
        available = _wait_for_embedding(
            self.memory_manager.provider,
            TEST_USER_ID,
            expected_count=2,
            timeout=30.0,
        )
        assert available, (
            "Timed out waiting for 2 memories to become "
            "retrievable in Mem0/ChromaDB"
        )

        # --- Step 4: Register user_id so injector can find it ---
        # Simulate what MemoryManager.address_request does when
        # a memory is written with a user_id.
        self.memory_manager._register_user_id(TEST_USER_ID)

        # --- Step 5: Build ContextInjector and inject ---
        injector = ContextInjector(
            self.memory_manager, self.memory_config,
        )
        # Enable injection for this test
        injector.enabled = True
        injector.relevance_threshold = 0.0  # accept all
        injector.max_memories = 10

        query = LLMQuery(
            messages=[
                {"role": "user", "content": "Tell me about the project"},
            ],
            action_type="chat",
        )

        injected_query, diagnostics = injector.inject(
            "assistant_agent", query, user_id=TEST_USER_ID,
        )

        # --- Step 6: Assert injection happened ---
        assert diagnostics["auto_inject_enabled"] is True
        assert diagnostics["injected_count"] >= 2, (
            f"Expected at least 2 injected memories, "
            f"got {diagnostics['injected_count']}"
        )

        # --- Step 7: Assert source agents ---
        source_agents = set(diagnostics["source_agents"])
        assert "profile_agent" in source_agents, (
            f"Expected 'profile_agent' in sources, "
            f"got {source_agents}"
        )
        assert "task_agent" in source_agents, (
            f"Expected 'task_agent' in sources, "
            f"got {source_agents}"
        )

        # --- Step 8: Assert memory types ---
        memory_types = set(diagnostics["memory_types"])
        assert "profile" in memory_types
        assert "task_context" in memory_types

        # --- Step 9: Assert content was formatted (not raw JSON) ---
        # The injected system message should contain natural
        # language from MemoryFormatter, not raw JSON.
        injected_system = injected_query.messages[0]
        assert injected_system["role"] == "system"
        content_block = injected_system["content"]

        # Profile formatting produces "User profile:" prefix
        assert "User profile:" in content_block, (
            "Expected formatted profile text in injection, "
            f"got: {content_block[:200]}"
        )
        # Task context formatting produces
        # "Current task context:" prefix
        assert "Current task context:" in content_block, (
            "Expected formatted task context in injection, "
            f"got: {content_block[:200]}"
        )

        # Raw JSON should NOT appear
        assert '{"name":' not in content_block
        assert '{"project":' not in content_block

        # --- Step 10: Assert resolved_user_id in diagnostics ---
        assert diagnostics["resolved_user_id"] == TEST_USER_ID
