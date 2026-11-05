# AIOS Shared Memory System — Complete Technical Reference

## What This Document Covers

This document describes the **cross-agent shared memory personalization system** implemented in the AIOS kernel. It covers how multiple AI agents can write memories about the same human user, how those memories are automatically injected into LLM prompts to personalize responses, and how strict user isolation prevents one user's data from leaking into another user's context.

---

## 1. High-Level Architecture

AIOS is an "AI Agent Operating System" — a kernel that manages multiple AI agents communicating over HTTP. The shared memory system allows a team of agents (e.g., a ProfileAgent, TaskAgent, and AssistantAgent) to collaboratively build a personalized understanding of a human user.

```
┌─────────────────────────────────────────────────────────────────────┐
│                        AIOS Kernel                                   │
│                                                                     │
│  ┌───────────────┐    ┌──────────────────┐    ┌─────────────────┐  │
│  │ ProfileAgent  │    │   TaskAgent      │    │ AssistantAgent  │  │
│  │ writes:       │    │ writes:          │    │ reads all       │  │
│  │ - user prefs  │    │ - current project│    │ shared memories │  │
│  │ - user name   │    │ - experiment     │    │ before each     │  │
│  │ - tools used  │    │ - goals/blockers │    │ LLM call        │  │
│  └──────┬────────┘    └──────┬───────────┘    └──────┬──────────┘  │
│         │                     │                       │             │
│         │  create_memory()    │  create_memory()      │ llm_chat()  │
│         │  sharing="shared"   │  sharing="shared"     │             │
│         ▼                     ▼                       ▼             │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │                    MemoryManager                              │  │
│  │  - Routes writes to Mem0Provider                             │  │
│  │  - Tracks known_user_ids for cross-agent discovery           │  │
│  │  - Owns the MemoryWriteBarrier                               │  │
│  └──────────────────────────────────┬───────────────────────────┘  │
│                                     │                               │
│  ┌──────────────────────────────────▼───────────────────────────┐  │
│  │                    Mem0Provider                               │  │
│  │  - Per-user ChromaDB collections (physical isolation)        │  │
│  │  - Hard user_id filter on every get_all() call               │  │
│  │  - Cross-agent sharing filter (_apply_sharing_filter)        │  │
│  └──────────────────────────────────┬───────────────────────────┘  │
│                                     │                               │
│  ┌──────────────────────────────────▼───────────────────────────┐  │
│  │              ChromaDB (Persistent Vector Store)               │  │
│  │  Collection: mem0_memories_alice_wu_8e4f21ab_kernel_shared   │  │
│  │  Collection: mem0_memories_bob_chen_3c7d90ef_kernel_shared   │  │
│  │  ... (one per user)                                          │  │
│  └──────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 2. Core Concepts

### 2.1 Memory Types

Each memory stored in the system has a `memory_type` metadata field:

| Type | Written By | Contains | Sharing |
|------|-----------|----------|---------|
| `profile` | ProfileAgent | User name, preferred language, tools, style | `shared` |
| `task_context` | TaskAgent | Current project, experiment, goals, blockers | `shared` |
| `conversation` | ConversationExtractor | User+assistant dialogue pairs | `private` |

### 2.2 Sharing Policy

Every memory has a `sharing_policy` metadata field:

- **`"shared"`**: visible to the agents in the owner's privilege group (see 2.5) working with the same user. ProfileAgent and TaskAgent write shared memories, and their privilege groups admit AssistantAgent, so AssistantAgent can read them.
- **`"private"`** — Visible ONLY to the agent that wrote it. Conversation memories are private by default.

### 2.3 User Identity

Each memory is scoped to a `user_id`. This is the human end-user's identity, NOT the agent name. Example: `"alice_wu_8e4f21ab__kernel_shared"`.

The `user_id` is the **primary isolation boundary**. No memory written for user Alice can ever appear in user Bob's LLM context.

### 2.4 Owner Agent

Each memory records which agent wrote it via `owner_agent`. The kernel sets this field to the calling agent's name on `add_memory`, whatever the caller sent. This enables the sharing rules:
- Same owner + private = visible to that agent only
- Different owner + shared = visible to the agents in the owner's privilege group, for that user
- Different owner + private = never visible

### 2.5 Privilege Groups

Following the access manager of the AIOS paper (Section 3.8), every agent owns a privilege group: the agents allowed to read and modify its shared memories. `AccessManager` (`aios/memory/access.py`) keeps the groups and exposes `add_privilege(sid, tid)` (put agent `sid` into agent `tid`'s group) and `check_access(sid, tid)`. Groups come from `memory.access_control.privilege_groups` in `config.yaml`. An agent outside the owner's group cannot see the owner's shared memories in auto-injection or search, and cannot get, update or remove them by id.

---

## 3. The Write Path

When an agent stores a memory, the following happens:

### 3.1 SDK Call → Kernel

An agent (e.g., ProfileAgent) calls:
```python
create_memory(
    agent_name="profile_agent",
    content='{"user_name": "Alice", "preferred_tools": ["VS Code", "Docker"]}',
    metadata={
        "user_id": "alice_wu_8e4f21ab__kernel_shared",
        "owner_agent": "profile_agent",
        "sharing_policy": "shared",
        "memory_type": "profile",
    }
)
```

### 3.2 MemoryManager Processing

The `MemoryManager.address_request()` method:

1. Converts the query into a `MemoryNote` object
2. Ensures `user_id` is present (falls back to agent_name if missing) and sets `owner_agent` to the calling agent
3. Registers the `user_id` in `_known_user_ids` for cross-agent discovery
4. Stamps the write barrier with `barrier.acquire(user_id)` → returns a sequence number
5. Calls `provider.add_memory(memory_note)`
6. On completion, calls `barrier.release(user_id, seq_no, success)` to notify waiting retrievals

### 3.3 Mem0Provider Storage

The `Mem0Provider.add_memory()` method:

1. Extracts `user_id` from the memory note's metadata
2. Calls `_get_client_for_user(user_id)` → returns a Mem0 Memory client scoped to a per-user ChromaDB collection
3. Stores the content as a vector embedding via `client.add(content, user_id=user_id, metadata={...}, infer=False)`
4. Waits for searchability via `_await_searchable()` polling
5. Returns `MemoryResponse(success=True, memory_id=...)`

### 3.4 Per-User Collection Routing

Each `user_id` gets its own ChromaDB collection. The naming convention is:
```
mem0_memories_{sanitized_user_id}
```

For example: `mem0_memories_alice_wu_8e4f21ab_kernel_shared`

This provides **physical isolation** — different users' memories live in completely separate vector stores. A query against Alice's collection can never return Bob's vectors.

---

## 4. The Read Path (Automatic Context Injection)

Before every LLM chat call, the `ContextInjector` automatically retrieves and injects relevant memories into the prompt.

### 4.1 Trigger

When `AssistantAgent` sends a chat LLM request with `user_id="alice_wu_8e4f21ab__kernel_shared"`, the `SyscallExecutor` calls:
```python
context_injector.inject(
    agent_name="assistant_agent",
    query=llm_query,
    user_id="alice_wu_8e4f21ab__kernel_shared",
)
```

### 4.2 Identity Resolution

`_resolve_user_id()` determines the memory partition:
- **If `user_id` is provided and differs from agent_name** → use it as the resolved identity
- **If `user_id` is None** → return None (only agent's own memories retrieved, no shared retrieval)

The resolved identity becomes `own_query_user_id = resolved_user_id or agent_name`.

### 4.3 Own-Memory Retrieval

First retrieval call fetches the agent's own memories for this user:
```python
MemoryQuery(params={
    "content": "user's latest message text",
    "k": 10,
    "agent_name": "assistant_agent",
    "user_id": "alice_wu_8e4f21ab__kernel_shared",
})
```

This goes to `Mem0Provider.retrieve_memory()` which:
1. Routes to Alice's per-user collection via `_get_client_for_user()`
2. Calls `client.get_all(filters={"user_id": "alice_wu_8e4f21ab__kernel_shared"})`
3. Returns all memories in that collection matching the hard `user_id` filter

### 4.4 Shared-Memory Retrieval

If `resolved_user_id` is set and differs from `agent_name`, a second retrieval fetches shared memories from other agents:
```python
MemoryQuery(params={
    "content": "user's latest message text",
    "k": 40,  # 4× over-fetch for post-filtering headroom
    "user_id": "alice_wu_8e4f21ab__kernel_shared",
    "sharing_policy": "shared",
    "agent_name": "assistant_agent",
})
```

The provider applies `_apply_sharing_filter()` which keeps only memories where:
- `metadata.user_id == "alice_wu_8e4f21ab__kernel_shared"` AND
- `metadata.sharing_policy == "shared"`

### 4.5 Merge and Deduplication

Own results and shared results are merged. Duplicates (by content string) are removed, with own-memory results taking priority.

### 4.6 Filtering Pipeline

The merged candidates go through a multi-stage filter:

1. **Relevance Threshold** — Memories with `score < relevance_threshold` (default 0.3) are dropped
2. **User-Partition Filter** — `metadata["user_id"]` must exactly match the resolved `own_query_user_id`. Memories with missing or mismatched user_id are excluded (fail-closed). This is defense-in-depth.
3. **Access Filter**: only memories where `owner_agent == agent_name` (own) OR `sharing_policy == "shared"` with the requesting agent in the owner's privilege group (cross-agent) survive
4. **Score Sorting** — Remaining memories sorted by relevance score descending
5. **Natural Language Formatting** — JSON content converted to readable sentences via `MemoryFormatter`
6. **Token Budget Truncation** — Least-relevant memories dropped until the block fits within `max_memory_tokens` (default 2000)

### 4.7 Prompt Injection

Surviving memories are formatted into a system message and prepended to the LLM query:

```
===== MEMORY CONTEXT =====
The following are relevant memories from prior interactions with this user.
Use them to personalize your response:

- [] User profile: Their name is Alice. They prefer coding in Python. They like using VS Code, Docker.
- [] Current task context: Working on project Dynamic Form Builder. Running experiment: Testing conditional rendering.

===== END MEMORY CONTEXT =====
```

The LLM then sees this context and personalizes its response accordingly.

---

## 5. Security Model — User Isolation

### 5.1 Defense in Depth (Three Layers)

The system uses three independent isolation mechanisms. Any single one is sufficient; all three run simultaneously:

| Layer | Where | Mechanism |
|-------|-------|-----------|
| 1. Physical Collection Routing | `Mem0Provider._get_client_for_user()` | Each user_id maps to a separate ChromaDB collection. A query against Alice's collection physically cannot return Bob's vectors. |
| 2. Hard Metadata Filter | `client.get_all(filters={"user_id": X})` | ChromaDB WHERE clause — only records with matching user_id in metadata are returned. |
| 3. ContextInjector User-Partition Filter | `context_injector.py` line 360 | After all retrieval, any memory where `metadata["user_id"] != resolved_user_id` is excluded. Fail-closed on missing metadata. |

### 5.2 Access Matrix

| Same User? | Owner Relation | Sharing Policy | Result |
|------------|----------------|----------------|--------|
| Yes | Same agent (own memory) | Private | **ALLOW** |
| Yes | Same agent | Shared | **ALLOW** |
| Yes | Different agent | Private | **DENY** |
| Yes | Different agent, in owner's privilege group | Shared | **ALLOW** |
| Yes | Different agent, not in owner's privilege group | Shared | **DENY** |
| No | Any agent | Private | **DENY** |
| No | Any agent | Shared | **DENY** |
| Missing user_id | Any | Any | **DENY** (fail-closed) |

### 5.3 Identity Comparison

Identities are compared as **exact strings**. No prefix matching, normalization, or substring checks:
- `"alice"` ≠ `"alice__kernel_shared"`
- `"alice__kernel_shared"` ≠ `"bob__kernel_shared"`

---

## 6. Write Barrier (Write-Before-Read Ordering)

### 6.1 The Problem

ProfileAgent and TaskAgent write shared memories, then AssistantAgent reads them — all in rapid succession. Without coordination, AssistantAgent's retrieval might execute before ProfileAgent's write commits to ChromaDB.

### 6.2 The Solution

The `MemoryWriteBarrier` enforces write-before-read ordering per user_id:

1. **Acceptance-time stamping**: When a `create_memory` syscall is accepted, `barrier.acquire(user_id)` assigns a monotonically-increasing sequence number
2. **Retrieval snapshot**: Before any retrieval, `barrier.snapshot(user_id)` captures the current high-water mark
3. **Wait on snapshot**: `barrier.wait_until_drained(user_id, snapshot)` blocks until all writes with `seq_no ≤ snapshot` have committed (or failed, or timed out)
4. **Release on commit**: After `provider.add_memory()` returns, `barrier.release(user_id, seq_no, success)` notifies waiting retrievals

### 6.3 Safety Properties

- **Bounded wait**: `timeout_ms` (default 5000ms) caps any retrieval's wait. On timeout, retrieval proceeds fail-open.
- **Failed writes still release**: A provider error doesn't strand retrievals.
- **No-op for non-Mem0 providers**: InHouseProvider and ZepProvider commit synchronously; the barrier bypasses them.
- **Empty user_id bypasses**: Legacy agent-scoped retrievals never wait.

---

## 7. Conversation Extraction

### 7.1 Automatic Storage

After every LLM chat response, the `ConversationExtractor` stores the user+assistant exchange as a memory:

```python
ConversationExtractor.extract_async(
    agent_name="assistant_agent",
    user_message="What should I focus on?",
    assistant_message="Based on your project...",
    user_id="alice_wu_8e4f21ab__kernel_shared",
)
```

### 7.2 Properties

- Runs in a **daemon thread** — never blocks the LLM response
- Stores with `sharing_policy="private"` — only the writing agent can see it
- Uses the resolved `user_id` so conversations land in the correct per-user collection
- Content format: `"User: {message}\nAssistant: {response}"`

---

## 8. Natural Language Formatting

### 8.1 The Problem

Memories are stored as JSON (structured data from ProfileAgent/TaskAgent). Small LLMs struggle to interpret raw JSON injected into prompts.

### 8.2 The Solution

`MemoryFormatter.format_memory()` converts JSON to natural language at inject time:

| Memory Type | Input (JSON) | Output (Natural Language) |
|-------------|-------------|---------------------------|
| `profile` | `{"user_name": "Alice", "preferred_tools": ["VS Code"]}` | `"User profile: Their name is Alice. They like using VS Code."` |
| `task_context` | `{"current_project": "Form Builder", "goals": "Ship v1"}` | `"Current task context: Working on project Form Builder. Goals: Ship v1."` |
| `conversation` | `"User: Hello\nAssistant: Hi"` | Returned as-is |
| Unknown type | `{"key": "value"}` | `"Custom type: key: value."` |

Formatting is **pure and non-destructive** — stored content is never modified.

---

## 9. Configuration

All settings live in `aios/config/config.yaml` under the `memory:` section:

```yaml
memory:
  provider: "mem0"              # Backend: "in-house", "mem0", or "zep"
  auto_extract: true            # Store conversations as memories
  auto_inject: true             # Inject memories before LLM calls
  relevance_threshold: 0.3      # Min similarity score for injection
  max_injected_memories: 10     # Max memories per LLM call
  max_memory_tokens: 2000       # Token budget for memory block

  write_barrier:
    enabled: true               # Enforce write-before-read ordering
    timeout_ms: 5000            # Max wait before fail-open

  access_control:
    privilege_groups:           # owner agent -> agents admitted to its group
      profile_agent: ["assistant_agent"]
      task_agent: ["assistant_agent"]

  mem0:
    user_id: "default"          # Fallback user_id
    llm:
      provider: "ollama"
      config:
        model: "qwen2.5:7b"
        ollama_base_url: "http://localhost:11434"
    embedder:
      provider: "ollama"
      config:
        model: "nomic-embed-text"
        ollama_base_url: "http://localhost:11434"
    vector_store:
      provider: "chroma"
      config:
        collection_name: "mem0_memories"   # Prefix for per-user collections
        path: ".mem0/chroma"               # Persistent storage directory
```

---

## 10. Request Flow (End-to-End)

Here's the complete flow for a single personalized LLM call:

```
1. ProfileAgent → POST /query (add_memory, user_id="alice", sharing="shared")
   → MemoryManager stamps barrier, routes to Mem0Provider
   → Mem0Provider writes to collection "mem0_memories_alice_..."
   → barrier.release() notifies waiters

2. TaskAgent → POST /query (add_memory, user_id="alice", sharing="shared")
   → Same flow as above

3. AssistantAgent → POST /query (llm_chat, user_id="alice")
   → SyscallExecutor detects action_type="chat"
   → Calls context_injector.inject(agent="assistant_agent", user_id="alice")
     a. resolve_user_id() → "alice"
     b. barrier.wait_until_drained("alice", snapshot) → waits for steps 1&2
     c. provider.retrieve_memory(user_id="alice") → own memories
     d. provider.retrieve_memory(user_id="alice", sharing="shared") → shared
     e. Merge, filter (user-partition → sharing-policy → relevance → tokens)
     f. Format to natural language
     g. Prepend as system message to LLM query
   → LLM sees personalized context, generates response
   → ConversationExtractor stores the exchange (async, private)
   → Response returned to agent
```

---

## 11. File Map

| File | Purpose |
|------|---------|
| `aios/memory/context_injector.py` | Retrieves memories and injects them into LLM prompts |
| `aios/memory/conversation_extractor.py` | Stores conversation turns as memories (async) |
| `aios/memory/manager.py` | Orchestrates providers, barrier, user_id registry, access checks |
| `aios/memory/access.py` | Privilege groups for cross-agent memory access |
| `aios/memory/write_barrier.py` | Enforces write-before-read ordering per user_id |
| `aios/memory/memory_formatter.py` | Converts JSON memories to natural language |
| `aios/memory/providers/mem0.py` | Mem0 + ChromaDB provider with per-user collections |
| `aios/memory/providers/base.py` | Abstract provider interface + sharing filter |
| `aios/memory/providers/factory.py` | Provider registry and factory |
| `aios/memory/note.py` | MemoryNote data class |
| `aios/config/config.yaml` | All configuration |
| `runtime/launch.py` | Kernel startup, wires components together |

---

## 12. Diagnostics

Every `inject()` call returns a diagnostics dict alongside the modified query:

```python
{
    "auto_inject_enabled": True,
    "candidate_count": 6,       # Memories before filtering
    "injected_count": 4,        # Memories after all filters
    "source_agents": ["profile_agent", "task_agent", "assistant_agent"],
    "memory_types": ["profile", "task_context", "conversation"],
    "prompt_tokens_before": 45,
    "prompt_tokens_after": 312,
    "resolved_user_id": "alice_wu_8e4f21ab__kernel_shared",
    "barrier_waits": [
        {"user_id": "alice_wu_8e4f21ab__kernel_shared", "outcome": "DRAINED"}
    ],
}
```

---

## 13. Testing

The system has comprehensive test coverage in `tests/modules/memory/`:

| Test File | Coverage |
|-----------|----------|
| `test_mem0_cross_user_isolation.py` | User-partition defense-in-depth filter |
| `test_context_injector_access_matrix.py` | Full 8-case sharing matrix + edge cases |
| `test_context_injector_explicit_user_id.py` | Cross-agent injection pipeline |
| `test_mem0_provider_user_filter.py` | Hard filter contract at Mem0 client level |
| `test_mem0_cross_user_retrieval.py` | Provider-level cross-user isolation |
| `test_mem0_cross_agent_retrieval.py` | Shared memory retrieval with promoted keys |
| `test_mem0_provider_searchability.py` | Write polling and visibility scenarios |
| `test_write_barrier_unit.py` | Barrier acquire/release/wait mechanics |
| `test_write_barrier_integration.py` | Full barrier scenarios with executor |
| `test_user_id_scoping_integration.py` | Multi-user sequential trials |
| `test_user_id_scoping_preservation.py` | Backward compatibility invariants |

All tests run offline with mocked providers — no live Mem0, ChromaDB, or Ollama needed.

---

## 14. Known Limitations

1. **`known_user_ids` is in-memory only** — On kernel restart, the registry is empty until agents write memories. Mitigated by explicit `user_id` in requests.

2. **Legacy unscoped memories are excluded** — Memories written before user_id scoping was introduced (missing `metadata["user_id"]`) are fail-closed excluded. They require explicit migration.

3. **Small model fact extraction** — Mem0's `infer=True` mode uses an LLM to extract facts. Small models (e.g., qwen2.5:7b) often produce unparseable output, resulting in zero stored facts. AIOS uses `infer=False` to bypass this and store raw content directly.

4. **Cross-restart recall with local models** — Mem0's embedding quality with local models (nomic-embed-text) may differ from cloud models, affecting retrieval relevance scores.
