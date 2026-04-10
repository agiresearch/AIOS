"""
Mem0 Provider Test Script
=========================
Tests the Mem0Provider through MemoryManager directly (no scheduler/queue needed).

Prerequisites:
  1. ollama pull nomic-embed-text
  2. pip install mem0ai --upgrade   (replaces the stub 0.0.1 package)
  3. Set memory.provider = "mem0" in aios/config/config.yaml

Run:
  python scripts/test_mem0_provider.py
"""

import sys
import os
import time

# Ensure project root (3 levels up from tests/modules/memory/) is on the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

# ── Colour helpers ────────────────────────────────────────────────────────────
GREEN  = "\033[92m"
RED    = "\033[91m"
YELLOW = "\033[93m"
RESET  = "\033[0m"

def ok(msg):   print(f"  {GREEN}PASS{RESET}  {msg}")
def fail(msg): print(f"  {RED}FAIL{RESET}  {msg}"); RESULTS.append(("FAIL", msg))
def info(msg): print(f"  {YELLOW}INFO{RESET}  {msg}")

RESULTS = []

def record(label, passed, detail=""):
    if passed:
        ok(label)
        RESULTS.append(("PASS", label))
    else:
        fail(f"{label} — {detail}")


# ── Preflight checks ──────────────────────────────────────────────────────────
def preflight():
    print("\n── Preflight ────────────────────────────────────────────────────────")

    # 1. Real mem0 importable?
    try:
        from mem0 import Memory  # noqa: F401
        ok("mem0 library importable")
    except ImportError:
        fail("mem0 not importable — run: pip install mem0ai --upgrade")
        sys.exit(1)

    # 2. Ollama reachable?
    import urllib.request
    try:
        urllib.request.urlopen("http://localhost:11434/api/tags", timeout=3)
        ok("Ollama reachable at localhost:11434")
    except Exception:
        fail("Ollama not reachable — start Ollama first")
        sys.exit(1)

    # 3. Config provider set to mem0?
    from aios.config.config_manager import config as cfg
    memory_cfg = cfg.get_memory_config() or {}
    provider = memory_cfg.get("provider", "in-house")
    if provider != "mem0":
        fail(f"config.yaml memory.provider = '{provider}' — change it to 'mem0'")
        sys.exit(1)
    ok(f"config.yaml memory.provider = 'mem0'")

    # 4. nomic-embed-text pulled?
    import json, urllib.request as req
    try:
        with req.urlopen("http://localhost:11434/api/tags", timeout=3) as r:
            models = [m["name"] for m in json.loads(r.read()).get("models", [])]
        if any("nomic-embed-text" in m for m in models):
            ok("nomic-embed-text model available in Ollama")
        else:
            fail(f"nomic-embed-text not pulled — run: ollama pull nomic-embed-text\n"
                 f"         Available models: {models}")
            sys.exit(1)
    except Exception as e:
        fail(f"Could not check Ollama models: {e}")
        sys.exit(1)


# ── Test helpers ──────────────────────────────────────────────────────────────
def make_syscall(operation_type: str, params: dict):
    """Build a MemorySyscall directly — circular import is now fixed in source."""
    from cerebrum.memory.apis import MemoryQuery
    from aios.syscall.memory import MemorySyscall
    query = MemoryQuery(operation_type=operation_type, params=params)
    return MemorySyscall(agent_name="test_agent", query=query)


def call(manager, operation_type: str, params: dict):
    """Call manager.address_request and return the MemoryResponse."""
    syscall = make_syscall(operation_type, params)
    return manager.address_request(syscall)


# ── Individual tests ──────────────────────────────────────────────────────────
def test_add_memory(manager):
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
    print("\n── Test 2: get_memory ───────────────────────────────────────────────")
    if not memory_id:
        info("Skipping — no memory_id from add_memory")
        return

    resp = call(manager, "get_memory", {"memory_id": memory_id})
    record("get_memory returns success=True", resp.success, getattr(resp, "error", ""))
    content = getattr(resp, "content", "") or ""
    record("get_memory returns non-empty content", bool(content), f"got: '{content}'")


def test_retrieve_memory(manager):
    print("\n── Test 3: retrieve_memory (semantic search) ────────────────────────")
    # Give Mem0 a moment to index
    time.sleep(1)
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


def test_update_memory(manager, memory_id):
    print("\n── Test 4: update_memory ────────────────────────────────────────────")
    if not memory_id:
        info("Skipping — no memory_id from add_memory")
        return

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
    # retrieve_memory_raw returns a list of MemoryNote objects
    if isinstance(result, list):
        record("retrieve_memory_raw returns a list", True)
        record("retrieve_memory_raw list is non-empty", len(result) >= 1,
               f"got {len(result)} items")
        if result:
            from aios.memory.note import MemoryNote
            record("items are MemoryNote instances", isinstance(result[0], MemoryNote),
                   f"got {type(result[0])}")
            info(f"First raw note content: \"{result[0].content}\"")
    else:
        # Some providers wrap in MemoryResponse
        record("retrieve_memory_raw returns a result", bool(result),
               f"got type {type(result)}")


def test_remove_memory(manager, memory_id):
    print("\n── Test 6: remove_memory ────────────────────────────────────────────")
    if not memory_id:
        info("Skipping — no memory_id from add_memory")
        return

    resp = call(manager, "remove_memory", {"memory_id": memory_id})
    record("remove_memory returns success=True", resp.success, getattr(resp, "error", ""))


def test_persistence(manager):
    """
    Persistence test: store a uniquely-tagged memory, then re-create the
    MemoryManager (simulating a restart) and verify the memory is still found.

    NOTE: This test is skipped with chromadb >= 1.0 because Mem0's bundled
    ChromaDB adapter uses the deprecated chromadb.Client(Settings(...)) API
    which does not persist data reliably in chromadb 1.x. Mem0 would need to
    be updated to use chromadb.PersistentClient() for this to work.
    """
    print("\n── Test 7: persistence across manager restart ───────────────────────")

    # Detect chromadb version — skip if >= 1.0
    try:
        import chromadb as _chroma
        major = int(_chroma.__version__.split(".")[0])
        if major >= 1:
            info(f"Skipping persistence test — chromadb {_chroma.__version__} uses "
                 f"PersistentClient but Mem0's adapter still calls the deprecated "
                 f"Client(Settings(...)) which doesn't persist in chromadb 1.x")
            RESULTS.append(("SKIP", "persistence — chromadb 1.x adapter limitation in Mem0"))
            return
    except Exception:
        pass
    unique_tag = f"persist_test_{int(time.time())}"

    # Store
    resp = call(manager, "add_memory", {
        "content": f"Persistence check memory with tag {unique_tag}",
        "tags": [unique_tag],
        "category": "Test"
    })
    if not resp.success:
        record("persistence: add before restart succeeded", False, getattr(resp, "error", ""))
        return

    time.sleep(1)

    # Simulate restart by creating a fresh MemoryManager
    from aios.memory.manager import MemoryManager
    manager2 = MemoryManager(provider="mem0")

    resp2 = call(manager2, "retrieve_memory", {
        "content": f"persistence check {unique_tag}",
        "k": 5
    })
    results = getattr(resp2, "search_results", []) or []
    found = any(unique_tag in str(r.get("content", "")) or
                unique_tag in str(r.get("tags", ""))
                for r in results)
    record("memory survives MemoryManager re-instantiation", found,
           f"searched for tag '{unique_tag}', got {len(results)} results")
    manager2.close()


# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    preflight()

    print("\n── Initialising MemoryManager (provider=mem0) ───────────────────────")
    try:
        from aios.memory.manager import MemoryManager
        manager = MemoryManager(provider="mem0")
        ok("MemoryManager initialised")
    except Exception as e:
        fail(f"MemoryManager init failed: {e}")
        import traceback; traceback.print_exc()
        sys.exit(1)

    memory_id = test_add_memory(manager)
    test_get_memory(manager, memory_id)
    test_retrieve_memory(manager)
    test_update_memory(manager, memory_id)
    test_retrieve_memory_raw(manager)
    test_remove_memory(manager, memory_id)
    test_persistence(manager)

    manager.close()

    # ── Summary ───────────────────────────────────────────────────────────────
    print("\n── Results ──────────────────────────────────────────────────────────")
    passed = sum(1 for s, _ in RESULTS if s == "PASS")
    failed = sum(1 for s, _ in RESULTS if s == "FAIL")
    skipped = sum(1 for s, _ in RESULTS if s == "SKIP")
    total  = passed + failed
    print(f"  {GREEN}{passed}/{total} passed{RESET}  {RED}{failed} failed{RESET}  {YELLOW}{skipped} skipped{RESET}")
    for status, label in RESULTS:
        colour = GREEN if status == "PASS" else (RED if status == "FAIL" else YELLOW)
        print(f"  {colour}{status}{RESET}  {label}")
    print()
    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
