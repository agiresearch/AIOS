"""
Unit tests for the FastAPI endpoints in ``runtime/launch.py``.

Uses FastAPI's TestClient with mocked kernel components — no real
LLM, memory, or storage services are invoked.

Import strategy: ``runtime.launch`` calls ``_ensure_initialized()``
at import time, which triggers real component construction. We patch
the heavy init functions and ``useSysCall`` before importing the app
module, using ``importlib`` for a controlled import.

Deviations from plan assumptions (confirmed from source):
- GET /status returns {"status": "ok"} (not just 200 with no body).
- Degraded state returns {"status": "warning"} with inactive_components list.
- POST /query for LLM uses asyncio.to_thread(execute_request, ...).
- Invalid query_type is caught by Pydantic's Literal validation → 422.
- Missing required LLM fields on /query triggers a 500 (generic exception handler),
  not a 422 — this is the real behavior, not necessarily desired but confirmed.
"""
import importlib
import sys
from unittest.mock import MagicMock, patch

import pytest


# ------------------------------------------------------------------
# Fixture: load the app with mocked initialization
# ------------------------------------------------------------------

@pytest.fixture()
def client():
    """Create a TestClient with all heavy init patched out.

    Patches are applied BEFORE importing the launch module so that
    the import-time ``_ensure_initialized()`` call doesn't trigger
    real component construction.
    """
    # Remove cached module if present from prior test
    mod_name = "runtime.launch"
    if mod_name in sys.modules:
        del sys.modules[mod_name]

    mock_execute_request = MagicMock()
    mock_syscall_wrapper = MagicMock()
    mock_executor = MagicMock()

    patches = [
        patch(
            "aios.hooks.modules.llm.useCore",
            return_value=MagicMock(),
        ),
        patch(
            "aios.hooks.modules.memory.useMemoryManager",
            return_value=MagicMock(),
        ),
        patch(
            "aios.hooks.modules.storage.useStorageManager",
            return_value=MagicMock(),
        ),
        patch(
            "aios.hooks.modules.tool.useToolManager",
            return_value=MagicMock(),
        ),
        patch(
            "aios.hooks.modules.agent.useFactory",
            return_value=(MagicMock(), MagicMock()),
        ),
        patch(
            "aios.hooks.modules.scheduler.fifo_scheduler_nonblock",
            return_value=MagicMock(),
        ),
        patch(
            "aios.hooks.modules.scheduler.rr_scheduler_nonblock",
            return_value=MagicMock(),
        ),
        patch(
            "aios.syscall.syscall.useSysCall",
            return_value=(
                mock_execute_request,
                mock_syscall_wrapper,
                mock_executor,
            ),
        ),
    ]

    for p in patches:
        p.start()

    try:
        # Import the module fresh with patches active
        launch = importlib.import_module("runtime.launch")
        # Replace the module-level execute_request with our mock
        launch.execute_request = mock_execute_request
        # Set active_components to a controlled dict
        launch.active_components = {
            "llms": MagicMock(),
            "storage": MagicMock(),
            "memory": MagicMock(),
            "tool": MagicMock(),
            "scheduler": MagicMock(),
            "factory": {
                "submit": MagicMock(),
                "await": MagicMock(),
            },
        }
        # Reset selected_llms
        launch.selected_llms = {"llms": []}

        from fastapi.testclient import TestClient
        tc = TestClient(launch.app)
        tc._mock_execute_request = mock_execute_request
        tc._launch = launch
        yield tc
    finally:
        for p in patches:
            p.stop()
        # Clean up module cache
        if mod_name in sys.modules:
            del sys.modules[mod_name]


# ------------------------------------------------------------------
# GET /status
# ------------------------------------------------------------------

class TestStatusEndpoint:
    """GET /status."""

    def test_all_active_returns_ok(self, client):
        resp = client.get("/status")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        assert "active" in data["message"].lower()

    def test_some_inactive_returns_warning(self, client):
        # Set some components to None
        client._launch.active_components["tool"] = None
        client._launch.active_components["memory"] = None

        resp = client.get("/status")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "warning"
        assert "tool" in data["inactive_components"]
        assert "memory" in data["inactive_components"]


# ------------------------------------------------------------------
# POST /user/select/llms + GET /user/selected/llms round-trip
# ------------------------------------------------------------------

class TestLLMSelection:
    """LLM selection endpoints."""

    def test_select_and_retrieve_llms(self, client):
        payload = [
            {"name": "gpt-4o", "backend": "openai"},
        ]
        resp = client.post("/user/select/llms", json=payload)
        assert resp.status_code == 200
        assert resp.json()["status"] == "success"

        resp = client.get("/user/selected/llms")
        assert resp.status_code == 200
        assert resp.json()["status"] == "success"
        assert "gpt-4o" in resp.json()["message"]

    def test_no_selection_returns_warning(self, client):
        resp = client.get("/user/selected/llms")
        assert resp.status_code == 200
        assert resp.json()["status"] == "warning"


# ------------------------------------------------------------------
# POST /query: LLM
# ------------------------------------------------------------------

class TestQueryLLM:
    """POST /query with query_type='llm'."""

    def test_llm_query_calls_execute_request(self, client):
        client._mock_execute_request.return_value = {
            "response": "hello world"
        }
        payload = {
            "agent_name": "test_agent",
            "query_type": "llm",
            "query_data": {
                "messages": [{"role": "user", "content": "hi"}],
                "action_type": "chat",
            },
        }
        resp = client.post("/query", json=payload)
        assert resp.status_code == 200
        client._mock_execute_request.assert_called_once()
        # Check agent_name was first arg
        call_args = client._mock_execute_request.call_args
        assert call_args[0][0] == "test_agent"

    def test_llm_query_with_user_id_promotion(self, client):
        """user_id in query_data promoted to top-level QueryRequest."""
        client._mock_execute_request.return_value = {
            "response": "ok"
        }
        payload = {
            "agent_name": "agent_a",
            "query_type": "llm",
            "query_data": {
                "messages": [{"role": "user", "content": "hi"}],
                "action_type": "chat",
                "user_id": "promoted_user",
            },
        }
        resp = client.post("/query", json=payload)
        assert resp.status_code == 200
        # The promotion happens in model_validator; verify via
        # the query object passed to execute_request having
        # _request_user_id set
        call_args = client._mock_execute_request.call_args
        query_arg = call_args[0][1]
        assert hasattr(query_arg, "_request_user_id")
        assert query_arg._request_user_id == "promoted_user"


# ------------------------------------------------------------------
# POST /query: memory
# ------------------------------------------------------------------

class TestQueryMemory:
    """POST /query with query_type='memory'."""

    def test_memory_query_routes_correctly(self, client):
        client._mock_execute_request.return_value = {
            "response": "stored"
        }
        payload = {
            "agent_name": "mem_agent",
            "query_type": "memory",
            "query_data": {
                "operation_type": "add_memory",
                "params": {"content": "remember this"},
            },
        }
        resp = client.post("/query", json=payload)
        assert resp.status_code == 200
        client._mock_execute_request.assert_called_once()
        call_args = client._mock_execute_request.call_args
        assert call_args[0][0] == "mem_agent"


# ------------------------------------------------------------------
# POST /query: validation errors
# ------------------------------------------------------------------

class TestQueryValidation:
    """Request validation via Pydantic."""

    def test_invalid_query_type_returns_422(self, client):
        """Pydantic's Literal["llm","tool","storage","memory"]
        rejects unknown types with 422."""
        payload = {
            "agent_name": "agent",
            "query_type": "invalid_type",
            "query_data": {},
        }
        resp = client.post("/query", json=payload)
        assert resp.status_code == 422

    def test_missing_agent_name_returns_422(self, client):
        payload = {
            "query_type": "llm",
            "query_data": {
                "messages": [{"role": "user", "content": "hi"}],
                "action_type": "chat",
            },
        }
        resp = client.post("/query", json=payload)
        assert resp.status_code == 422

    def test_missing_query_data_returns_422(self, client):
        payload = {
            "agent_name": "agent",
            "query_type": "llm",
        }
        resp = client.post("/query", json=payload)
        assert resp.status_code == 422


# ------------------------------------------------------------------
# POST /query: exception in execute_request → 500
# ------------------------------------------------------------------

class TestQueryErrors:
    """Error paths in the /query handler."""

    def test_execute_request_exception_returns_500(self, client):
        """When execute_request raises, handler catches and returns 500."""
        client._mock_execute_request.side_effect = RuntimeError(
            "kernel exploded"
        )
        payload = {
            "agent_name": "agent",
            "query_type": "memory",
            "query_data": {
                "operation_type": "add_memory",
                "params": {"content": "boom"},
            },
        }
        resp = client.post("/query", json=payload)
        assert resp.status_code == 500
        assert "kernel exploded" in resp.json()["detail"]
