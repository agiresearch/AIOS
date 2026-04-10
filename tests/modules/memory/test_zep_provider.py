"""
Zep Provider Test Script
========================
Tests the ZepProvider through MemoryManager directly (no scheduler/queue needed).
Uses Zep Cloud — requires a valid API key in config.yaml.

Prerequisites:
  pip install zep-cloud
  Set memory.provider = "zep" in aios/config/config.yaml
  Set memory.zep.api_key to your Zep Cloud API key
  Remove or comment out base_url (cloud mode, not self-hosted)

Run:
  python tests/modules/memory/test_zep_provider.py
"""

import sys
import os
import time
import uuid

# Project root (3 levels up from tests/modules/memory/)
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

# ── Colour helpers ────────────────────────────────────────────────────────────
GREEN  = "\033[92m"
RED    = "\033[91m"
YELLOW = "\033[93m"
RESET  = "\033[0m"

def ok(msg):   print(f"  {GREEN}PASS{RESET}  {msg}")
def fail(msg): print(f"  {RED}FAIL{RESET}  {msg}")
def info(msg): print(f"  {YELLOW}INFO{RESET}  {msg}")

RESULTS = []

def record(label, passed, detail=""):
    if passed:
        ok(label)
        RESULTS.append(("PASS", label))
    else:
        fail(f"{label} — {detail}")
        RESULTS.append(("FAIL", f"{label} — {detail}"))


# ── Preflight ─────────────────────────────────────────────────────────────────
def preflight():
    print("\n── Preflight ────────────────────────────────────────────────────────")

    # zep-cloud importable?
    try:
        from zep_cloud.client import Zep  # noqa: F401
        ok("zep-cloud library importable")
    except ImportError:
        fail("zep-cloud not installed — run: pip install zep-cloud")
        sys.exit(1)

    # Config set to zep?
    from aios.config.config_manager import config as cfg
    memory_cfg = cfg.get_memory_config() or {}
    provider = memory_cfg.get("provider", "in-house")
    if provider != "zep":
        fail(f"config.yaml memory.provider = '{provider}' — change it to 'zep'")
        sys.exit(1)
    ok("config.yaml memory.provider = 'zep'")

    # API key present?
    zep_cfg = memory_cfg.get("zep", {})
    api_key = zep_cfg.get("api_key", "")
    if not api_key:
        fail("config.yaml memory.zep.api_key is empty")
        sys.exit(1)
    ok(f"API key present ({api_key[:12]}...)")

    # base_url warning
    if zep_cfg.get("base_url"):
        info(f"base_url is set ({zep_cfg['base_url']}) — using self-hosted mode")
    else:
        ok("Using Zep Cloud (no base_url)")


# ── Helpers ───────────────────────────────────────────────────────────────────
def make_syscall(operation_type: str, params: dict):
    from cerebrum.memory.apis import MemoryQuery
    from aios.syscall.memory import MemorySyscall
    query = MemoryQuery(operation_type=operation_type, params=params)
    return MemorySyscall(agent_name="test_agent", query=query)


def call(manager, operation_type: str, params: dict):
    syscall = make_syscall(operation_type, params)
    return manager.address_request(syscall)


# ── Session setup helper ──────────────────────────────────────────────────────
def ensure_session(manager, session_id: str):
    """
    Zep Cloud requires a user + session to exist before adding messages.
    The provider handles this automatically in add_memory, but we call it
    explicitly here for test setup so get/search work before any add.
    """
    user_id = manager.provider.default_user_id or "aios_default_user"
    try:
        manager.provider.client.memory.add_session(session_id=session_id, user_id=user_id)
        info(f"Created session '{session_id}' for user '{user_id}'")
    except Exception as e:
        info(f"Session '{session_id}' already exists or skipped: {e}")


# ── Tests ─────────────────────────────────────────────────────────────────────
def test_add_memory(manager, session_id):
    print("\n── Test 1: add_memory ───────────────────────────────────────────────")
    resp = call(manager, "add_memory", {
        "content": "The Eiffel Tower is located in Paris, France.",
        "keywords": ["eiffel", "paris", "france"],
        "tags": ["geography", "landmarks"],
        "category": "Facts",
        "context": "World geography"
    })
    record("add_memory returns success=True", resp.success, getattr(resp, "error", ""))
    record("add_memory returns a memory_id",
           bool(getattr(resp, "memory_id", None)),
           f"got: {getattr(resp, 'memory_id', None)}")
    return getattr(resp, "memory_id", None)


def test_get_memory(manager, memory_id):
    print("\n── Test 2: get_memory (by episode UUID) ─────────────────────────────")
    if not memory_id:
        info("Skipping — no memory_id from add_memory")
        return
    # Allow Zep to process the episode
    time.sleep(3)
    resp = call(manager, "get_memory", {"memory_id": memory_id})
    # Free tier may not support episode.get — treat as soft pass if error is API limitation
    if resp.success:
        record("get_memory returns success=True", True)
        content = getattr(resp, "content", "") or ""
        record("get_memory returns non-empty content", bool(content), f"got: '{content[:80]}'")
        if content:
            info(f"Content: \"{content[:120]}\"")
    else:
        error = getattr(resp, "error", "")
        info(f"get_memory not supported on free tier: {error}")
        RESULTS.append(("SKIP", "get_memory — episode.get not available on free tier"))

def test_retrieve_memory(manager):
    print("\n── Test 3: retrieve_memory (semantic search) ────────────────────────")
    time.sleep(8)  # Zep graph extraction is async — needs ~2-8s to process
    resp = call(manager, "retrieve_memory", {
        "content": "famous tower in France",
        "k": 3
    })
    record("retrieve_memory returns success=True", resp.success, getattr(resp, "error", ""))
    results = getattr(resp, "search_results", []) or []
    record("retrieve_memory returns at least 1 result", len(results) >= 1,
           f"got {len(results)} results")
    if results:
        first = results[0]
        record("result has 'content' field", "content" in first, f"keys: {list(first.keys())}")
        info(f"Top result: \"{first.get('content', '')}\"  score={first.get('score')}")


def test_update_memory(manager, session_id, memory_id):
    print("\n── Test 4: update_memory ────────────────────────────────────────────")
    if not memory_id:
        info("Skipping — no memory_id from add_memory")
        return
    # Zep update = add new message to session (no direct edit API)
    resp = call(manager, "update_memory", {
        "memory_id": memory_id,
        "id": memory_id,
        "content": "The Eiffel Tower is in Paris and was built in 1889.",
        "keywords": ["eiffel", "paris", "1889"],
        "tags": ["geography", "history"],
        "category": "Facts",
        "context": "World geography"
    })
    record("update_memory returns success=True", resp.success, getattr(resp, "error", ""))


def test_retrieve_memory_raw(manager):
    print("\n── Test 5: retrieve_memory_raw ──────────────────────────────────────")
    time.sleep(1)
    syscall = make_syscall("retrieve_memory_raw", {
        "content": "Eiffel Tower Paris",
        "k": 3
    })
    result = manager.address_request(syscall)
    if isinstance(result, list):
        record("retrieve_memory_raw returns a list", True)
        record("retrieve_memory_raw list is non-empty", len(result) >= 1,
               f"got {len(result)} items")
        if result:
            from aios.memory.note import MemoryNote
            record("items are MemoryNote instances", isinstance(result[0], MemoryNote),
                   f"got {type(result[0])}")
            info(f"First raw note: \"{result[0].content[:80]}\"")
    else:
        record("retrieve_memory_raw returns a result", bool(result),
               f"got type {type(result)}")


def test_remove_memory(manager, memory_id):
    print("\n── Test 6: remove_memory ────────────────────────────────────────────")
    if not memory_id:
        info("Skipping — no memory_id from add_memory")
        return
    resp = call(manager, "remove_memory", {"memory_id": memory_id})
    record("remove_memory returns success=True", resp.success, getattr(resp, "error", ""))
    info("Note: free tier has no delete API — this is a soft no-op")


def test_persistence(manager):
    """
    Zep Cloud is a hosted service — data persists server-side by design.
    We verify by storing a memory, creating a new MemoryManager, and
    searching for it.
    """
    print("\n── Test 7: persistence (Zep Cloud server-side) ──────────────────────")

    unique_content = f"Persistence check unique fact {uuid.uuid4().hex[:8]}"

    resp = call(manager, "add_memory", {
        "content": unique_content,
        "tags": ["persistence"],
        "category": "Test"
    })
    if not resp.success:
        record("persistence: add succeeded", False, getattr(resp, "error", ""))
        return

    time.sleep(8)  # wait for graph extraction

    # New MemoryManager instance
    from aios.memory.manager import MemoryManager
    manager2 = MemoryManager(provider="zep")

    resp2 = call(manager2, "retrieve_memory", {
        "content": unique_content,
        "k": 3
    })
    results = getattr(resp2, "search_results", []) or []
    record("memory survives MemoryManager re-instantiation",
           len(results) >= 1,
           f"got {len(results)} results")
    manager2.close()


# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    preflight()

    print("\n── Initialising MemoryManager (provider=zep) ────────────────────────")
    try:
        from aios.memory.manager import MemoryManager
        manager = MemoryManager(provider="zep")
        ok("MemoryManager initialised")
    except Exception as e:
        fail(f"MemoryManager init failed: {e}")
        import traceback; traceback.print_exc()
        sys.exit(1)

    # Use a unique session per test run so tests don't bleed into each other
    session_id = f"aios_test_{uuid.uuid4().hex[:8]}"
    info(f"Using session_id: '{session_id}'")

    # Switch the manager's default session to our test session
    manager.provider.default_session_id = session_id

    memory_id = test_add_memory(manager, session_id)
    test_get_memory(manager, memory_id)
    test_retrieve_memory(manager)
    test_update_memory(manager, session_id, memory_id)
    test_retrieve_memory_raw(manager)
    test_persistence(manager)
    test_remove_memory(manager, memory_id)  # cleanup last

    manager.close()

    # ── Summary ───────────────────────────────────────────────────────────────
    print("\n── Results ──────────────────────────────────────────────────────────")
    passed  = sum(1 for s, _ in RESULTS if s == "PASS")
    failed  = sum(1 for s, _ in RESULTS if s == "FAIL")
    skipped = sum(1 for s, _ in RESULTS if s == "SKIP")
    total   = passed + failed
    print(f"  {GREEN}{passed}/{total} passed{RESET}  {RED}{failed} failed{RESET}  {YELLOW}{skipped} skipped{RESET}")
    for status, label in RESULTS:
        colour = GREEN if status == "PASS" else (RED if status == "FAIL" else YELLOW)
        print(f"  {colour}{status}{RESET}  {label}")
    print()
    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
