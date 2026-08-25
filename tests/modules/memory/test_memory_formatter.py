"""
Unit tests for ``aios.memory.memory_formatter.format_memory``.

Pure function — no mocks of external services needed.
"""
import json

import pytest

from aios.memory.memory_formatter import format_memory


# ------------------------------------------------------------------
# Profile formatting
# ------------------------------------------------------------------

class TestProfileFormatting:
    """Tests for memory_type="profile"."""

    def test_profile_all_known_keys(self):
        content = json.dumps({
            "name": "Alice",
            "language": "Python",
            "tools": "VS Code",
            "style": "concise",
        })
        result = format_memory(content, {"memory_type": "profile"})
        assert result == (
            "User profile: Their name is Alice. "
            "They prefer coding in Python. "
            "They like using VS Code. "
            "They prefer a concise response style."
        )

    def test_profile_subset_of_keys(self):
        content = json.dumps({"name": "Bob", "style": "verbose"})
        result = format_memory(content, {"memory_type": "profile"})
        assert "Their name is Bob." in result
        assert "They prefer a verbose response style." in result
        # Keys not present should not appear
        assert "coding in" not in result
        assert "using" not in result

    def test_profile_with_extra_unknown_keys(self):
        content = json.dumps({
            "name": "Charlie",
            "favourite_editor": "vim",
        })
        result = format_memory(content, {"memory_type": "profile"})
        assert "Their name is Charlie." in result
        # Extra key gets generic formatting
        assert "favourite_editor: vim." in result

    def test_profile_list_value_joined(self):
        content = json.dumps({
            "tools": ["pytest", "mypy", "ruff"],
        })
        result = format_memory(content, {"memory_type": "profile"})
        assert "They like using pytest, mypy, ruff." in result

    def test_profile_empty_dict(self):
        content = json.dumps({})
        result = format_memory(content, {"memory_type": "profile"})
        assert result == "User profile:"

    def test_profile_non_json_content_passthrough(self):
        content = "I like Python"
        result = format_memory(content, {"memory_type": "profile"})
        assert result == "I like Python"

    def test_profile_json_array_passthrough(self):
        content = json.dumps(["a", "b", "c"])
        result = format_memory(content, {"memory_type": "profile"})
        assert result == content


# ------------------------------------------------------------------
# Task-context formatting
# ------------------------------------------------------------------

class TestTaskContextFormatting:
    """Tests for memory_type="task_context"."""

    def test_task_context_all_known_keys(self):
        content = json.dumps({
            "project": "AIOS",
            "experiment": "memory barrier",
            "goals": "fix race condition",
            "blockers": "flaky test",
            "next_steps": "add retry logic",
        })
        result = format_memory(content, {"memory_type": "task_context"})
        assert result == (
            "Current task context: Working on project AIOS. "
            "Running experiment: memory barrier. "
            "Goals: fix race condition. "
            "Blockers: flaky test. "
            "Next steps: add retry logic."
        )

    def test_task_context_subset_of_keys(self):
        content = json.dumps({"project": "Cerebrum", "goals": "ship v2"})
        result = format_memory(
            content, {"memory_type": "task_context"}
        )
        assert "Working on project Cerebrum." in result
        assert "Goals: ship v2." in result
        assert "experiment" not in result.lower()

    def test_task_context_with_extra_keys(self):
        content = json.dumps({
            "project": "AIOS",
            "priority": "high",
        })
        result = format_memory(
            content, {"memory_type": "task_context"}
        )
        assert "Working on project AIOS." in result
        assert "priority: high." in result

    def test_task_context_list_value_in_goals(self):
        content = json.dumps({
            "goals": ["ship", "test", "deploy"],
        })
        result = format_memory(
            content, {"memory_type": "task_context"}
        )
        assert "Goals: ship, test, deploy." in result

    def test_task_context_empty_dict(self):
        content = json.dumps({})
        result = format_memory(
            content, {"memory_type": "task_context"}
        )
        assert result == "Current task context:"


# ------------------------------------------------------------------
# Conversation passthrough
# ------------------------------------------------------------------

class TestConversationPassthrough:
    """Tests for memory_type="conversation"."""

    def test_conversation_plain_text(self):
        content = "User asked about Python GIL"
        result = format_memory(
            content, {"memory_type": "conversation"}
        )
        assert result == content

    def test_conversation_json_content_still_passthrough(self):
        content = json.dumps({"user": "hi", "assistant": "hello"})
        result = format_memory(
            content, {"memory_type": "conversation"}
        )
        # Conversation always passes through regardless of JSON
        assert result == content


# ------------------------------------------------------------------
# Unknown memory_type (generic formatting)
# ------------------------------------------------------------------

class TestUnknownMemoryType:
    """Tests for unrecognised memory_type values with valid JSON."""

    def test_unknown_type_generic_format(self):
        content = json.dumps({"status": "active", "role": "admin"})
        result = format_memory(
            content, {"memory_type": "user_preferences"}
        )
        # Label: "User preferences:" (underscores → spaces, capitalised)
        assert result.startswith("User preferences:")
        assert "status: active." in result
        assert "role: admin." in result

    def test_unknown_type_underscore_in_keys(self):
        content = json.dumps({"first_name": "Dana"})
        result = format_memory(
            content, {"memory_type": "custom_data"}
        )
        # Key underscores converted to spaces
        assert "first name: Dana." in result
        assert result.startswith("Custom data:")

    def test_unknown_type_non_json_passthrough(self):
        content = "just plain text"
        result = format_memory(
            content, {"memory_type": "some_unknown"}
        )
        assert result == "just plain text"


# ------------------------------------------------------------------
# Missing memory_type (empty string or absent key)
# ------------------------------------------------------------------

class TestMissingMemoryType:
    """Tests when memory_type is missing or empty."""

    def test_missing_type_valid_json_generic_format(self):
        content = json.dumps({"key": "value"})
        result = format_memory(content, {})
        # Uses "Memory:" as the label
        assert result.startswith("Memory:")
        assert "key: value." in result

    def test_empty_type_valid_json_generic_format(self):
        content = json.dumps({"x": 42})
        result = format_memory(content, {"memory_type": ""})
        assert result.startswith("Memory:")
        assert "x: 42." in result

    def test_missing_type_non_json_passthrough(self):
        content = "hello world"
        result = format_memory(content, {})
        assert result == "hello world"

    def test_missing_type_json_array_passthrough(self):
        content = json.dumps([1, 2, 3])
        result = format_memory(content, {})
        assert result == content

    def test_missing_type_empty_dict(self):
        content = json.dumps({})
        result = format_memory(content, {})
        assert result == "Memory:"


# ------------------------------------------------------------------
# Invalid/edge-case content
# ------------------------------------------------------------------

class TestEdgeCases:
    """Edge cases: invalid JSON, arrays, empty strings."""

    def test_invalid_json_content_passthrough(self):
        content = "{not valid json"
        result = format_memory(
            content, {"memory_type": "profile"}
        )
        assert result == content

    def test_empty_string_content(self):
        result = format_memory("", {"memory_type": "profile"})
        # Empty string is not valid JSON → passthrough
        assert result == ""

    def test_json_array_with_known_type_passthrough(self):
        content = json.dumps(["item1", "item2"])
        result = format_memory(
            content, {"memory_type": "task_context"}
        )
        # _try_parse_json returns None for arrays
        assert result == content


# ------------------------------------------------------------------
# Exception path (forced error)
# ------------------------------------------------------------------

class TestExceptionFallback:
    """Verifies the try/except fallback returns raw content."""

    def test_metadata_get_raises(self, monkeypatch):
        """If metadata.get() raises, format_memory returns raw
        content instead of propagating the exception."""
        content = "some important memory"

        class BadDict(dict):
            def get(self, *args, **kwargs):
                raise RuntimeError("deliberate failure")

        result = format_memory(content, BadDict())
        assert result == content

    def test_none_metadata_handled(self):
        """Synthetic: None isn't the declared arg type, but verifies
        the except-branch safety net returns raw content rather than
        propagating an AttributeError if a caller violates the type
        contract.  Not a real production failure mode — purely a
        defensive-coding smoke test."""
        content = "raw fallback"
        result = format_memory(content, None)  # type: ignore[arg-type]
        assert result == content
