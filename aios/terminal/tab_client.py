"""Scheduling-aware client helpers for an AIOS terminal tab.

Every LLM request the terminal sends becomes a *syscall* in the kernel, and the
kernel's scheduling policy decides the order in which queued syscalls reach the
model. Two things are needed to make that visible from a terminal tab:

1. the request must carry a ``priority`` -- ``runtime/launch.py`` reads it and
   stamps it onto the syscall, which is what the ``priority`` policy sorts on;
2. each tab should submit as its own agent with its own model, so the kernel log
   shows *which* tab is waiting and for what.

Neither is expressible through ``cerebrum.llm.apis.llm_chat``: its payload is
fixed and has no ``priority`` field. This module therefore builds the same
payload the SDK builds, plus the top-level ``priority`` the kernel already
accepts, and posts it with the standard library.

Tab -> model -> priority
------------------------
================  =====================  ===================
``--model``       model                  priority
================  =====================  ===================
``ollama``        local ``llama3``       ``high``
``gemini``        ``gemini-2.5-flash``   ``normal`` (medium)
``groq``          ``openai/gpt-oss-20b`` ``low``
================  =====================  ===================

The model is what the kernel routes on, so its ``name`` must match an entry in
the kernel's ``config.yaml`` (Ollama models are also registered on demand).
The priority is only acted on while the kernel runs ``scheduler.policy:
priority``; ``fifo`` and ``round_robin`` accept the field and ignore it, so the
same tabs behave sensibly under all three policies -- which is exactly what a
policy comparison needs.

The module deliberately uses only the standard library and imports nothing from
the kernel, so a tab starts instantly and needs neither the kernel's
dependencies nor a model backend.
"""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

#: Priorities the kernel's priority policy understands, most urgent first.
PRIORITIES: Tuple[str, ...] = ("high", "normal", "low")

#: Level assumed when a request carries none (matches the kernel default).
DEFAULT_PRIORITY = "normal"

#: Textual spellings accepted for each level, all case-insensitive.
_PRIORITY_ALIASES: Dict[str, str] = {
    "high": "high",
    "hi": "high",
    "urgent": "high",
    "critical": "high",
    "interactive": "high",
    "normal": "normal",
    "med": "normal",
    "medium": "normal",
    "default": "normal",
    "low": "low",
    "bg": "low",
    "background": "low",
    "batch": "low",
}

#: Which backend submits at which priority. This is the convention the demo
#: runs on: the local model is the interactive one, the slowest hosted model is
#: the batch one.
BACKEND_PRIORITIES: Dict[str, str] = {
    "ollama": "high",
    "gemini": "normal",
    "groq": "low",
}

#: The model each tab key submits with. ``name`` must match a model configured
#: in the kernel's ``config.yaml``; ``backend`` must match its ``backend`` key.
TAB_MODELS: Dict[str, Dict[str, str]] = {
    "ollama": {"name": "llama3", "backend": "ollama"},
    "gemini": {"name": "gemini-2.5-flash", "backend": "gemini"},
    "groq": {"name": "openai/gpt-oss-20b", "backend": "groq"},
}

#: A model call can take minutes on a local backend, so the read timeout is a
#: safety net against a hung kernel, not a scheduling signal.
DEFAULT_TIMEOUT = 900.0


class KernelUnreachable(Exception):
    """Raised when the kernel cannot be reached or rejects a request."""


# ----------------------------------------------------------------------
# Priority and model resolution
# ----------------------------------------------------------------------
def normalise_priority(value: Any) -> str:
    """Return the canonical level for a user-supplied priority.

    Accepts ``"high"``, ``"medium"``, ``"normal"``, ``"low"`` and the other
    spellings in :data:`_PRIORITY_ALIASES`.

    Raises:
        ValueError: If the value is not a level this terminal understands.
    """
    key = str(value).strip().lower()
    level = _PRIORITY_ALIASES.get(key)
    if level is None:
        raise ValueError(
            f"unknown priority {value!r}; choose from {list(PRIORITIES)}"
        )
    return level


def priority_for_backend(backend: Optional[str]) -> Optional[str]:
    """Return the priority configured for a backend, or ``None`` if unset."""
    if not backend:
        return None
    return BACKEND_PRIORITIES.get(str(backend).strip().lower())


def resolve_model(spec: str) -> Dict[str, str]:
    """Return the ``{"name", "backend"}`` entry the kernel should route to.

    Three forms are accepted:

    * a tab key -- ``"ollama"``, ``"gemini"``, ``"groq"``;
    * a model name from :data:`TAB_MODELS` -- ``"gemini-2.5-flash"``;
    * ``"<backend>:<model name>"`` for another model on a known backend --
      ``"groq:openai/gpt-oss-120b"``.

    Raises:
        ValueError: If the spec matches nothing, listing the known keys.
    """
    key = str(spec).strip()
    if not key:
        raise ValueError("no model given")

    lowered = key.lower()
    for tab_key, model in TAB_MODELS.items():
        if lowered == tab_key or lowered == model["backend"].lower():
            return dict(model)
    for model in TAB_MODELS.values():
        if key == model["name"]:
            return dict(model)

    backend, _, name = key.partition(":")
    backend = backend.strip().lower()
    if name and backend in BACKEND_PRIORITIES:
        return {"name": name.strip(), "backend": backend}

    options = ", ".join(sorted(TAB_MODELS))
    raise ValueError(
        f"unknown model {spec!r}; choose a tab key ({options}), one of "
        f"{[model['name'] for model in TAB_MODELS.values()]}, or "
        f"'<backend>:<model name>' for a backend in {list(BACKEND_PRIORITIES)}"
    )


def tab_table() -> List[Tuple[str, str, str, str]]:
    """Return ``(tab key, model, backend, priority)`` for each known tab."""
    return [
        (key, model["name"], model["backend"], BACKEND_PRIORITIES[model["backend"]])
        for key, model in TAB_MODELS.items()
    ]


# ----------------------------------------------------------------------
# Kernel transport
# ----------------------------------------------------------------------
def _request(
    url: str,
    payload: Optional[Mapping[str, Any]] = None,
    timeout: float = DEFAULT_TIMEOUT,
) -> Any:
    """Send a GET (``payload is None``) or POST to the kernel and decode JSON."""
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    request = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST" if data is not None else "GET",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as error:
        detail = error.read().decode("utf-8", "replace")
        raise KernelUnreachable(
            f"kernel returned HTTP {error.code}: {detail[:300]}"
        )
    except (urllib.error.URLError, TimeoutError, OSError) as error:
        raise KernelUnreachable(
            f"could not reach the kernel at {url} ({error}).\n"
            f"  Is it running?  Start it with: scripts/run_kernel.sh"
        )
    except Exception as error:  # a body that is not JSON, for instance
        raise KernelUnreachable(
            f"unexpected response from the kernel at {url} ({error})"
        )


def _base(server: str) -> str:
    """Return a server URL without a trailing slash."""
    return str(server).rstrip("/")


def build_llm_payload(
    agent_name: str,
    messages: Sequence[Mapping[str, Any]],
    action_type: str = "chat",
    priority: Optional[str] = None,
    model: Optional[Mapping[str, str]] = None,
    tools: Optional[Sequence[Any]] = None,
) -> Dict[str, Any]:
    """Build the ``POST /query`` body for one LLM request.

    Mirrors what ``cerebrum.llm.apis`` sends, plus the per-request ``priority``
    the kernel reads. The two fields live at different depths, and neither
    placement is optional:

    * ``priority`` is **top level**, because ``runtime/launch.py`` reads
      ``request.priority`` off the request body and stamps it onto the syscall;
    * ``llms`` is **inside ``query_data``**, because the kernel reads
      ``request.query_data.llms`` when it builds the query -- which is where the
      Cerebrum SDK puts it too. Sent at the top level it is silently dropped by
      the request model, and every tab falls back to the kernel's first model.
    """
    query_data: Dict[str, Any] = {
        "messages": list(messages),
        "action_type": action_type,
    }
    if tools is not None:
        query_data["tools"] = list(tools)
    if model:
        query_data["llms"] = [dict(model)]

    payload: Dict[str, Any] = {
        "agent_name": agent_name,
        "query_type": "llm",
        "query_data": query_data,
    }
    if priority:
        payload["priority"] = priority
    return payload


def post_query(
    server: str,
    payload: Mapping[str, Any],
    timeout: float = DEFAULT_TIMEOUT,
) -> Dict[str, Any]:
    """Submit one request to ``POST /query`` and return the decoded body."""
    return _request(f"{_base(server)}/query", payload, timeout=timeout)


def extract_reply(body: Mapping[str, Any]) -> str:
    """Pull the assistant message out of a ``POST /query`` response."""
    response = (body or {}).get("response", "")
    if isinstance(response, dict):
        if response.get("error"):
            return f"[kernel error] {response['error']}"
        return str(response.get("response_message", response))
    if hasattr(response, "response_message"):
        return str(response.response_message)
    return str(response)


def kernel_status(server: str, timeout: float = 15.0) -> str:
    """Return the kernel's human-readable status."""
    try:
        body = _request(f"{_base(server)}/status", timeout=timeout)
    except KernelUnreachable as error:
        return str(error)
    return f"{body.get('status', 'unknown')}: {body.get('message', '')}"


def kernel_scheduler(server: str, timeout: float = 30.0) -> Dict[str, Any]:
    """Return the kernel's active scheduling policy description."""
    return _request(f"{_base(server)}/core/scheduler", timeout=timeout)


def kernel_models(server: str, timeout: float = 30.0) -> List[Dict[str, Any]]:
    """Return the model configurations the kernel has loaded."""
    body = _request(f"{_base(server)}/core/llms/list", timeout=timeout)
    return list(body.get("llms") or [])
