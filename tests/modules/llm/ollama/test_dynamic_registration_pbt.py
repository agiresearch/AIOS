"""
Property-based test: Bug Condition Exploration

Tests that _dynamic_register_ollama_model on LLMAdapter correctly
registers Ollama models available on the server but NOT listed in
config.yaml, making them pass check_availability_for_selected_llm_lists.

The fix path is: execute_llm_syscalls → _dynamic_register_ollama_model
→ _query_ollama_available_models → _initialize_single_llm, which adds
the model to available_llm_names. The utility function itself remains
a pure name-in-list check.

**Validates: Requirements 1.1, 1.2, 1.3, 1.4**
"""

import pytest
import threading
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

# Strategy: pick any model from the server-available-but-unconfigured set
ollama_unconfigured_model = st.sampled_from(SERVER_AVAILABLE_UNCONFIGURED)


def _make_ollama_tags_response():
    """Build a fake /api/tags JSON response."""
    return {
        "models": [{"name": m} for m in ALL_SERVER_MODELS]
    }


def _make_mock_adapter():
    """
    Create a minimal adapter-like object with the attributes
    that _dynamic_register_ollama_model needs, without going
    through the full LLMAdapter.__init__ (which requires config,
    API keys, etc.).
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
    # Router only needs a llm_configs attribute
    adapter.router = MagicMock()
    adapter.router.llm_configs = adapter.llm_configs
    return adapter


class TestBugConditionExploration:
    """
    Property 1: Bug Condition — Unlisted Ollama Model Rejected
    Despite Server Availability.

    Tests the ACTUAL fix path: _dynamic_register_ollama_model
    queries the Ollama server, registers the model, and then
    check_availability_for_selected_llm_lists returns [True].
    """

    @given(model_name=ollama_unconfigured_model)
    @settings(max_examples=20)
    def test_unconfigured_ollama_model_should_be_available(
        self, model_name: str
    ):
        """
        **Validates: Requirements 1.1, 1.2, 1.3**

        Bug condition: model is on the Ollama server but not in
        available_llm_names (populated only from config.yaml).

        After dynamic registration the model should appear in
        available_llm_names and check_availability returns [True].
        """
        adapter = _make_mock_adapter()

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = _make_ollama_tags_response()
        mock_resp.raise_for_status = MagicMock()

        with patch("aios.llm_core.adapter.requests.get",
                    return_value=mock_resp):
            registered = adapter._dynamic_register_ollama_model(
                model_name
            )

        assert registered is True, (
            f"_dynamic_register_ollama_model returned False for "
            f"'{model_name}' which is on the server"
        )
        assert model_name in adapter.available_llm_names, (
            f"'{model_name}' not in available_llm_names after "
            f"dynamic registration"
        )

        selected_llm_list = [
            {"name": model_name, "backend": "ollama"}
        ]
        result = check_availability_for_selected_llm_lists(
            adapter.available_llm_names, [selected_llm_list]
        )
        assert result == [True], (
            f"After dynamic registration, "
            f"check_availability returned {result} instead of "
            f"[True] for '{model_name}'"
        )

    def test_concrete_bug_case_qwen3_4b(self):
        """
        **Validates: Requirements 1.1, 1.4**

        Concrete reproduction: qwen3:4b is on the Ollama server,
        qwen3:1.7b is the only configured model.

        After dynamic registration, check_availability returns
        [True].
        """
        adapter = _make_mock_adapter()

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = _make_ollama_tags_response()
        mock_resp.raise_for_status = MagicMock()

        with patch("aios.llm_core.adapter.requests.get",
                    return_value=mock_resp):
            registered = adapter._dynamic_register_ollama_model(
                "qwen3:4b"
            )

        assert registered is True, (
            "_dynamic_register_ollama_model returned False for "
            "qwen3:4b"
        )

        result = check_availability_for_selected_llm_lists(
            adapter.available_llm_names,
            [[{"name": "qwen3:4b", "backend": "ollama"}]],
        )
        assert result == [True], (
            f"After dynamic registration, check_availability "
            f"returned {result} for qwen3:4b. Expected [True]."
        )


# ---------------------------------------------------------------------------
# Property 2: Preservation — Configured and Non-Ollama Model Behavior
# ---------------------------------------------------------------------------
#
# These tests verify that EXISTING correct behavior of
# check_availability_for_selected_llm_lists is preserved.
# They MUST PASS on the current unfixed code.
#
# **Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.5**
# ---------------------------------------------------------------------------

import string


# Strategy: generate random model names that are guaranteed NOT to
# appear in any realistic Ollama server or config list.
# We prefix with "zz_fake_" to avoid collisions with real model names.
random_unavailable_model = st.text(
    alphabet=string.ascii_lowercase + string.digits,
    min_size=3,
    max_size=12,
).map(lambda s: f"zz_fake_{s}:latest")


class TestPreservation:
    """
    Property 2: Preservation — Configured and Non-Ollama Model
    Behavior Unchanged.

    All tests in this class MUST PASS on the current unfixed code.
    They capture baseline behaviour that the fix must not break.
    """

    # ------------------------------------------------------------------
    # 2.1  Configured model preservation (PBT)
    # ------------------------------------------------------------------
    @given(
        model_name=st.sampled_from(CONFIGURED_MODELS),
    )
    @settings(max_examples=20)
    def test_configured_model_is_available(self, model_name: str):
        """
        **Validates: Requirements 3.1**

        For any model that IS in available_llm_names (i.e. listed
        in config.yaml), check_availability must return [True].
        """
        selected_llm_list = [
            {"name": model_name, "backend": "ollama"}
        ]

        result = check_availability_for_selected_llm_lists(
            CONFIGURED_MODELS, [selected_llm_list]
        )

        assert result == [True], (
            f"Configured model '{model_name}' should be available "
            f"but got {result}"
        )

    # ------------------------------------------------------------------
    # 2.2  Truly unavailable model rejection (PBT)
    # ------------------------------------------------------------------
    @given(
        model_name=random_unavailable_model,
    )
    @settings(max_examples=50)
    def test_truly_unavailable_model_is_rejected(
        self, model_name: str
    ):
        """
        **Validates: Requirements 3.2**

        For any model name that is NOT in available_llm_names AND
        is not on any Ollama server (random gibberish names),
        check_availability must return [False].
        """
        selected_llm_list = [
            {"name": model_name, "backend": "ollama"}
        ]

        result = check_availability_for_selected_llm_lists(
            CONFIGURED_MODELS, [selected_llm_list]
        )

        assert result == [False], (
            f"Unavailable model '{model_name}' should be rejected "
            f"but got {result}"
        )

    # ------------------------------------------------------------------
    # 2.3  Mixed configured and unconfigured models
    # ------------------------------------------------------------------
    def test_mixed_configured_and_unconfigured_returns_false(self):
        """
        **Validates: Requirements 3.1, 3.2**

        When a single selected_llm_list contains BOTH a configured
        model AND an unconfigured model, the result must be [False]
        because ALL models in the list must be available.
        """
        selected_llm_list = [
            {"name": "qwen3:1.7b", "backend": "ollama"},
            {"name": "nonexistent:latest", "backend": "ollama"},
        ]

        result = check_availability_for_selected_llm_lists(
            CONFIGURED_MODELS, [selected_llm_list]
        )

        assert result == [False], (
            f"Mixed list with an unconfigured model should return "
            f"[False] but got {result}"
        )

    # ------------------------------------------------------------------
    # 2.4  Multiple requests with all configured models
    # ------------------------------------------------------------------
    def test_multiple_requests_all_configured(self):
        """
        **Validates: Requirements 3.1, 3.3**

        When multiple selected_llm_lists all contain only configured
        models, every result must be [True].
        """
        lists = [
            [{"name": "qwen3:1.7b", "backend": "ollama"}],
            [{"name": "qwen3:1.7b", "backend": "ollama"}],
            [{"name": "qwen3:1.7b", "backend": "ollama"}],
        ]

        result = check_availability_for_selected_llm_lists(
            CONFIGURED_MODELS, lists
        )

        assert result == [True, True, True], (
            f"All-configured requests should return all True "
            f"but got {result}"
        )

    # ------------------------------------------------------------------
    # 2.5  Empty available list
    # ------------------------------------------------------------------
    def test_empty_available_list_rejects_everything(self):
        """
        **Validates: Requirements 3.2, 3.5**

        When available_llm_names is empty, any request must return
        [False] regardless of what model is requested.
        """
        selected_llm_list = [
            {"name": "qwen3:1.7b", "backend": "ollama"}
        ]

        result = check_availability_for_selected_llm_lists(
            [], [selected_llm_list]
        )

        assert result == [False], (
            f"Empty available list should reject everything "
            f"but got {result}"
        )
