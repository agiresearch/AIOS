"""
Property-based test: Dynamic Ollama Model Registration

Tests that _dynamic_register_ollama_model on LLMAdapter correctly
registers Ollama models available on the server but NOT listed in
config.yaml, making them pass check_availability_for_selected_llm_lists.

The fix path is: execute_llm_syscalls -> _dynamic_register_ollama_model
-> _query_ollama_available_models -> _initialize_single_llm, which adds
the model to available_llm_names. The utility function itself remains
a pure name-in-list check.

**Validates: Requirements 1.1, 1.2, 1.3, 1.4, 3.1-3.5**
"""

import string
import threading
import unittest
from unittest.mock import patch, MagicMock

from hypothesis import given, settings
from hypothesis import strategies as st

from aios.llm_core.adapter import LLMAdapter, LLMConfig
from aios.llm_core.utils import (
    check_availability_for_selected_llm_lists,
)

# Models registered in the adapter (simulating config.yaml)
CONFIGURED_MODELS = ["qwen3:1.7b"]

# Models available on the Ollama server but NOT in config.yaml
SERVER_AVAILABLE_UNCONFIGURED = [
    "qwen3:4b",
    "qwen3:8b",
    "llama3:8b",
    "mistral:7b",
    "gemma2:9b",
]

# All models the fake Ollama server reports
ALL_SERVER_MODELS = CONFIGURED_MODELS + SERVER_AVAILABLE_UNCONFIGURED

# Strategy: pick from server-available-but-unconfigured set
ollama_unconfigured_model = st.sampled_from(
    SERVER_AVAILABLE_UNCONFIGURED
)

# Strategy: random model names guaranteed NOT to appear anywhere
random_unavailable_model = st.text(
    alphabet=string.ascii_lowercase + string.digits,
    min_size=3,
    max_size=12,
).map(lambda s: f"zz_fake_{s}:latest")


def _make_ollama_tags_response():
    """Build a fake /api/tags JSON response."""
    return {
        "models": [{"name": m} for m in ALL_SERVER_MODELS]
    }


def _make_mock_adapter():
    """
    Create a minimal adapter-like object with the attributes
    that _dynamic_register_ollama_model needs, without going
    through the full LLMAdapter.__init__.
    """
    adapter = object.__new__(LLMAdapter)
    adapter.available_llm_names = list(CONFIGURED_MODELS)
    adapter.llm_configs = [
        LLMConfig(
            name="qwen3:1.7b",
            backend="ollama",
            hostname="http://localhost:11434",
        )
    ]
    adapter.llms = ["ollama/qwen3:1.7b"]
    adapter._ollama_hostname = "http://localhost:11434"
    adapter._dynamic_registration_lock = threading.Lock()
    adapter.router = MagicMock()
    adapter.router.llm_configs = adapter.llm_configs
    return adapter


# ---------------------------------------------------------------
# Property 1: Bug Condition — Dynamic Registration Works
# ---------------------------------------------------------------

class TestBugConditionExploration(unittest.TestCase):
    """
    Tests the fix path: _dynamic_register_ollama_model queries
    the Ollama server, registers the model, and then
    check_availability_for_selected_llm_lists returns [True].
    """

    @given(model_name=ollama_unconfigured_model)
    @settings(max_examples=20)
    def test_unconfigured_ollama_model_should_be_available(
        self, model_name
    ):
        adapter = _make_mock_adapter()

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = (
            _make_ollama_tags_response()
        )
        mock_resp.raise_for_status = MagicMock()

        with patch(
            "aios.llm_core.adapter.requests.get",
            return_value=mock_resp,
        ):
            registered = (
                adapter._dynamic_register_ollama_model(
                    model_name
                )
            )

        self.assertTrue(
            registered,
            f"_dynamic_register_ollama_model returned False "
            f"for '{model_name}' which is on the server",
        )
        self.assertIn(model_name, adapter.available_llm_names)

        result = check_availability_for_selected_llm_lists(
            adapter.available_llm_names,
            [[{"name": model_name, "backend": "ollama"}]],
        )
        self.assertEqual(result, [True])

    def test_concrete_bug_case_qwen3_4b(self):
        adapter = _make_mock_adapter()

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = (
            _make_ollama_tags_response()
        )
        mock_resp.raise_for_status = MagicMock()

        with patch(
            "aios.llm_core.adapter.requests.get",
            return_value=mock_resp,
        ):
            registered = (
                adapter._dynamic_register_ollama_model(
                    "qwen3:4b"
                )
            )

        self.assertTrue(registered)
        result = check_availability_for_selected_llm_lists(
            adapter.available_llm_names,
            [[{"name": "qwen3:4b", "backend": "ollama"}]],
        )
        self.assertEqual(result, [True])


# ---------------------------------------------------------------
# Property 2: Preservation — Existing Behavior Unchanged
# ---------------------------------------------------------------

class TestPreservation(unittest.TestCase):
    """
    Verifies that EXISTING correct behavior of
    check_availability_for_selected_llm_lists is preserved.
    """

    @given(model_name=st.sampled_from(CONFIGURED_MODELS))
    @settings(max_examples=20)
    def test_configured_model_is_available(self, model_name):
        result = check_availability_for_selected_llm_lists(
            CONFIGURED_MODELS,
            [[{"name": model_name, "backend": "ollama"}]],
        )
        self.assertEqual(result, [True])

    @given(model_name=random_unavailable_model)
    @settings(max_examples=50)
    def test_truly_unavailable_model_is_rejected(
        self, model_name
    ):
        result = check_availability_for_selected_llm_lists(
            CONFIGURED_MODELS,
            [[{"name": model_name, "backend": "ollama"}]],
        )
        self.assertEqual(result, [False])

    def test_mixed_configured_and_unconfigured_returns_false(
        self,
    ):
        result = check_availability_for_selected_llm_lists(
            CONFIGURED_MODELS,
            [
                [
                    {"name": "qwen3:1.7b", "backend": "ollama"},
                    {
                        "name": "nonexistent:latest",
                        "backend": "ollama",
                    },
                ]
            ],
        )
        self.assertEqual(result, [False])

    def test_multiple_requests_all_configured(self):
        lists = [
            [{"name": "qwen3:1.7b", "backend": "ollama"}],
            [{"name": "qwen3:1.7b", "backend": "ollama"}],
            [{"name": "qwen3:1.7b", "backend": "ollama"}],
        ]
        result = check_availability_for_selected_llm_lists(
            CONFIGURED_MODELS, lists
        )
        self.assertEqual(result, [True, True, True])

    def test_empty_available_list_rejects_everything(self):
        result = check_availability_for_selected_llm_lists(
            [],
            [[{"name": "qwen3:1.7b", "backend": "ollama"}]],
        )
        self.assertEqual(result, [False])


if __name__ == "__main__":
    unittest.main()
