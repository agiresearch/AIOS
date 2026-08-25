"""
Unit tests for ``aios.memory.conversation_extractor.ConversationExtractor``.

Strategy: call ``_store_conversation`` directly (it's a separate method)
rather than letting a real daemon thread run, eliminating timing races.
The ``extract_async`` tests mock ``threading.Thread`` to verify the thread
is constructed with the right target/args without starting a live thread.
"""
import logging
from unittest.mock import MagicMock, patch

import pytest

from aios.memory.conversation_extractor import (
    ConversationExtractor,
)


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------

def _make_extractor(enabled=True):
    """Build a ConversationExtractor with a mock memory_manager."""
    mm = MagicMock()
    mm.provider = MagicMock()
    mm.provider.add_memory = MagicMock()
    config = {"auto_extract": enabled}
    extractor = ConversationExtractor(
        memory_manager=mm, config=config,
    )
    return extractor, mm


# ------------------------------------------------------------------
# Enabled/disabled control
# ------------------------------------------------------------------

class TestEnabledDisabled:
    """auto_extract toggle governs whether work is performed."""

    def test_disabled_does_not_spawn_thread(self):
        """When auto_extract=False, extract_async returns
        immediately without spawning a thread."""
        extractor, mm = _make_extractor(enabled=False)
        with patch(
            "aios.memory.conversation_extractor.threading.Thread"
        ) as mock_thread:
            extractor.extract_async(
                "agent_a", "hi", "hello", user_id="u1",
            )
            mock_thread.assert_not_called()
        mm.provider.add_memory.assert_not_called()

    def test_enabled_spawns_thread(self):
        """When auto_extract=True, a daemon thread is created
        with _store_conversation as target."""
        extractor, mm = _make_extractor(enabled=True)
        with patch(
            "aios.memory.conversation_extractor.threading.Thread"
        ) as mock_thread:
            mock_instance = MagicMock()
            mock_thread.return_value = mock_instance

            extractor.extract_async(
                "agent_a", "hi", "hello", user_id="u1",
            )

            mock_thread.assert_called_once_with(
                target=extractor._store_conversation,
                args=("agent_a", "hi", "hello", "u1"),
                daemon=True,
            )
            mock_instance.start.assert_called_once()


# ------------------------------------------------------------------
# _store_conversation: metadata correctness
# ------------------------------------------------------------------

class TestStoreConversation:
    """Direct calls to _store_conversation (no threads)."""

    def test_metadata_with_explicit_user_id(self):
        """user_id='alex' → effective_user_id is 'alex'."""
        extractor, mm = _make_extractor()
        extractor._store_conversation(
            "assistant_agent", "how are you?", "I'm fine!",
            user_id="alex",
        )
        mm.provider.add_memory.assert_called_once()
        note = mm.provider.add_memory.call_args[0][0]

        assert note.metadata["user_id"] == "alex"
        assert note.metadata["owner_agent"] == "assistant_agent"
        assert note.metadata["memory_type"] == "conversation"
        assert note.metadata["sharing_policy"] == "private"

    def test_metadata_user_id_none_falls_back_to_agent(self):
        """user_id=None → effective_user_id falls back to
        agent_name."""
        extractor, mm = _make_extractor()
        extractor._store_conversation(
            "my_agent", "question", "answer", user_id=None,
        )
        note = mm.provider.add_memory.call_args[0][0]
        assert note.metadata["user_id"] == "my_agent"

    def test_metadata_empty_string_user_id_falls_back(self):
        """user_id='' (falsy) → falls back to agent_name."""
        extractor, mm = _make_extractor()
        extractor._store_conversation(
            "bot", "q", "a", user_id="",
        )
        note = mm.provider.add_memory.call_args[0][0]
        assert note.metadata["user_id"] == "bot"

    def test_memory_note_content_format(self):
        """MemoryNote.content uses _build_conversation_content."""
        extractor, mm = _make_extractor()
        extractor._store_conversation(
            "agent", "what is Python?", "A programming language.",
            user_id="user1",
        )
        note = mm.provider.add_memory.call_args[0][0]
        expected = (
            "User: what is Python?\n"
            "Assistant: A programming language."
        )
        assert note.content == expected

    def test_memory_note_context_and_category(self):
        """MemoryNote is constructed with context='conversation'
        and category='conversation'."""
        extractor, mm = _make_extractor()
        extractor._store_conversation(
            "agent", "hi", "hello", user_id="u",
        )
        note = mm.provider.add_memory.call_args[0][0]
        assert note.context == "conversation"
        assert note.category == "conversation"


# ------------------------------------------------------------------
# _build_conversation_content (static method)
# ------------------------------------------------------------------

class TestBuildContent:
    """Pure static method — no mocks needed."""

    def test_basic_format(self):
        result = ConversationExtractor._build_conversation_content(
            "hello", "hi there",
        )
        assert result == "User: hello\nAssistant: hi there"

    def test_multiline_messages(self):
        result = ConversationExtractor._build_conversation_content(
            "line1\nline2", "resp1\nresp2",
        )
        assert result == (
            "User: line1\nline2\n"
            "Assistant: resp1\nresp2"
        )

    def test_empty_messages(self):
        result = ConversationExtractor._build_conversation_content(
            "", "",
        )
        assert result == "User: \nAssistant: "


# ------------------------------------------------------------------
# Error handling
# ------------------------------------------------------------------

class TestErrorHandling:
    """Errors in provider.add_memory are logged, not raised."""

    def test_add_memory_exception_logged_not_raised(self, caplog):
        """Provider raising doesn't propagate; WARNING is logged."""
        extractor, mm = _make_extractor()
        mm.provider.add_memory.side_effect = RuntimeError(
            "provider exploded"
        )

        with caplog.at_level(logging.WARNING):
            # Should not raise
            extractor._store_conversation(
                "agent", "q", "a", user_id="u",
            )

        assert "Conversation extraction failed" in caplog.text

    def test_thread_spawn_exception_logged(self, caplog):
        """If threading.Thread itself raises, extract_async logs
        a WARNING and doesn't crash.

        This tests a real try/except block in extract_async() that
        the author explicitly wrote as defensive code.  In practice,
        Thread() essentially never raises on valid args under normal
        CPython, so while the code path is real, the failure mode is
        near-unreachable in production (interpreter shutdown, resource
        exhaustion, or a misbehaving Thread subclass would be needed).
        """
        extractor, _ = _make_extractor(enabled=True)

        with patch(
            "aios.memory.conversation_extractor.threading.Thread",
            side_effect=RuntimeError("thread pool full"),
        ):
            with caplog.at_level(logging.WARNING):
                extractor.extract_async("a", "q", "a", user_id="u")

        assert "Failed to spawn extraction thread" in caplog.text
