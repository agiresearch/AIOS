"""Tests for terminal tabs that carry a scheduling priority.

A tab's job is small but easy to get subtly wrong: it must submit to the model
it claims to use, at the priority it claims to have, under the agent name it was
given. ``aios/terminal/tab_client.py`` holds that mapping and the request
payload, and ``aios/terminal/terminal.py`` the commands that change it, so both
can be exercised without a kernel, a model backend or an interactive console.

The behaviour worth being most careful about is the interaction between the two
ways a priority is chosen: derived from the tab's backend by default, or pinned
by the user. Switching model must not silently overwrite a pinned priority, and
``/priority auto`` must hand control back to the model.
"""

from __future__ import annotations

import pytest

from aios.terminal import tab_client
from aios.terminal.terminal import AIOSTerminal

MESSAGES = [{"role": "user", "content": "hello"}]


def make_tab(**kwargs) -> AIOSTerminal:
    """Return a tab that does not need a console or a kernel."""
    kwargs.setdefault("mode", "chat")
    return AIOSTerminal(**kwargs)


# ----------------------------------------------------------------------
# Backend -> priority
# ----------------------------------------------------------------------
def test_each_backend_carries_the_priority_the_demo_expects():
    assert tab_client.priority_for_backend("ollama") == "high"
    assert tab_client.priority_for_backend("gemini") == "normal"
    assert tab_client.priority_for_backend("groq") == "low"


def test_a_backend_without_a_convention_carries_no_priority():
    """A tab on some other backend sends no priority, so the kernel default applies."""
    assert tab_client.priority_for_backend(None) is None
    assert tab_client.priority_for_backend("openai") is None


@pytest.mark.parametrize(
    "spelling,expected",
    [
        ("high", "high"),
        ("HIGH", "high"),
        ("urgent", "high"),
        ("medium", "normal"),
        ("med", "normal"),
        ("normal", "normal"),
        ("low", "low"),
        ("background", "low"),
    ],
)
def test_priority_spellings_normalise_to_a_level(spelling, expected):
    assert tab_client.normalise_priority(spelling) == expected


def test_an_unknown_priority_is_rejected():
    """Better to refuse than to quietly schedule at the wrong level."""
    with pytest.raises(ValueError):
        tab_client.normalise_priority("yesterday")


# ----------------------------------------------------------------------
# Model resolution
# ----------------------------------------------------------------------
def test_a_tab_key_resolves_to_that_backend_and_model():
    model = tab_client.resolve_model("ollama")
    assert model["backend"] == "ollama"
    assert model == tab_client.TAB_MODELS["ollama"]


def test_a_model_name_resolves_back_to_its_tab():
    model = tab_client.resolve_model(tab_client.TAB_MODELS["gemini"]["name"])
    assert model["backend"] == "gemini"


def test_another_model_on_a_known_backend_can_be_named_directly():
    model = tab_client.resolve_model("groq:openai/gpt-oss-120b")
    assert model == {"name": "openai/gpt-oss-120b", "backend": "groq"}


def test_an_unknown_model_is_rejected_and_lists_the_alternatives():
    with pytest.raises(ValueError) as error:
        tab_client.resolve_model("banana")
    assert "ollama" in str(error.value)


def test_the_tab_table_covers_every_backend_with_a_priority():
    backends = {backend for _, _, backend, _ in tab_client.tab_table()}
    assert backends == set(tab_client.BACKEND_PRIORITIES)


# ----------------------------------------------------------------------
# Request payload
# ----------------------------------------------------------------------
def test_the_payload_carries_priority_model_and_agent():
    model = tab_client.resolve_model("groq")
    payload = tab_client.build_llm_payload(
        "groq_tab", MESSAGES, priority="low", model=model
    )
    assert payload["agent_name"] == "groq_tab"
    assert payload["query_type"] == "llm"
    assert payload["priority"] == "low"
    assert payload["query_data"]["messages"] == MESSAGES
    assert payload["query_data"]["action_type"] == "chat"


def test_the_model_is_sent_where_the_kernel_reads_it():
    """``llms`` belongs inside ``query_data``.

    The kernel builds the query from ``request.query_data.llms``. Sent at the
    top level it is dropped by the request model without an error, and the tab
    silently runs on the kernel's first model instead of the one it named.
    """
    model = tab_client.resolve_model("groq")
    payload = tab_client.build_llm_payload("groq_tab", MESSAGES, model=model)
    assert payload["query_data"]["llms"] == [model]
    assert "llms" not in payload


def test_the_priority_is_sent_where_the_kernel_reads_it():
    """``priority`` is a sibling of ``query_data``, not part of it."""
    payload = tab_client.build_llm_payload("terminal", MESSAGES, priority="high")
    assert payload["priority"] == "high"
    assert "priority" not in payload["query_data"]


def test_a_tab_without_priority_or_model_sends_neither():
    """Without them the kernel applies its own defaults, which is the old behaviour."""
    payload = tab_client.build_llm_payload("terminal", MESSAGES)
    assert "priority" not in payload
    assert "llms" not in payload["query_data"]
    assert "tools" not in payload["query_data"]


def test_file_operations_carry_their_tools():
    payload = tab_client.build_llm_payload(
        "terminal", MESSAGES, action_type="operate_file", tools=[]
    )
    assert payload["query_data"]["action_type"] == "operate_file"
    assert payload["query_data"]["tools"] == []


def test_the_reply_is_unwrapped_from_the_query_response():
    body = {"response": {"response_message": "LOW", "finished": True}}
    assert tab_client.extract_reply(body) == "LOW"


def test_a_kernel_side_error_is_surfaced_rather_than_swallowed():
    body = {"response": {"error": "Selected LLMs are not all available."}}
    assert "not all available" in tab_client.extract_reply(body)


# ----------------------------------------------------------------------
# The terminal's own state
# ----------------------------------------------------------------------
def test_a_tab_defaults_to_the_priority_of_its_model():
    tab = make_tab(model=tab_client.resolve_model("ollama"))
    assert tab.priority == "high"
    assert tab.priority_pinned is False


def test_an_explicit_priority_wins_over_the_model_default():
    tab = make_tab(model=tab_client.resolve_model("groq"), priority="high")
    assert tab.priority == "high"
    assert tab.priority_pinned is True


def test_pinning_a_priority_survives_a_model_change():
    tab = make_tab(model=tab_client.resolve_model("groq"))
    tab.handle_slash_command("/priority high")
    tab.handle_slash_command("/model gemini")
    assert tab.model["backend"] == "gemini"
    assert tab.priority == "high"


def test_auto_priority_follows_the_new_model():
    tab = make_tab(model=tab_client.resolve_model("ollama"))
    tab.handle_slash_command("/priority low")
    tab.handle_slash_command("/priority auto")
    assert tab.priority == "high"  # ollama again, not the pinned low

    tab.handle_slash_command("/model groq")
    assert tab.priority == "low"


def test_rename_changes_the_agent_identity():
    tab = make_tab(model=tab_client.resolve_model("gemini"))
    tab.handle_slash_command("/name urgent_tab")
    assert tab.agent_name == "urgent_tab"


@pytest.mark.parametrize("command", ["/priority nonsense", "/model nonsense"])
def test_a_bad_argument_changes_nothing(command):
    tab = make_tab(model=tab_client.resolve_model("gemini"), priority="normal")
    tab.handle_slash_command(command)
    assert tab.priority == "normal"
    assert tab.model["backend"] == "gemini"


def test_non_slash_input_is_left_to_the_chat_and_file_paths():
    tab = make_tab()
    assert tab.handle_slash_command("hello there") is False


def test_the_help_mentions_the_scheduling_commands(capsys):
    make_tab(model=tab_client.resolve_model("groq")).display_help()
    output = capsys.readouterr().out
    assert "priority" in output
    assert "scheduler" in output


# ----------------------------------------------------------------------
# Sending
# ----------------------------------------------------------------------
def test_a_chat_message_is_sent_with_this_tabs_priority_and_model(monkeypatch):
    sent = {}

    def fake_post(server, payload, timeout=tab_client.DEFAULT_TIMEOUT):
        sent.update(payload)
        return {"response": {"response_message": "hello back", "finished": True}}

    monkeypatch.setattr(tab_client, "post_query", fake_post)

    tab = make_tab(agent_name="groq_tab", model=tab_client.resolve_model("groq"))

    assert tab._send_chat("hello") == "hello back"
    assert sent["agent_name"] == "groq_tab"
    assert sent["priority"] == "low"
    assert sent["query_data"]["llms"] == [tab_client.TAB_MODELS["groq"]]
    assert tab.conversation_history[-1] == {
        "role": "assistant",
        "content": "hello back",
    }


def test_an_unreachable_kernel_is_reported_and_the_turn_is_not_recorded(monkeypatch):
    def explode(*args, **kwargs):
        raise tab_client.KernelUnreachable("could not reach the kernel")

    monkeypatch.setattr(tab_client, "post_query", explode)

    tab = make_tab()
    assert "could not reach the kernel" in tab._send_chat("hello")
    assert tab.conversation_history == []
