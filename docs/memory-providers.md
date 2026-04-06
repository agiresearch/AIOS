# Memory Providers

AIOS supports pluggable memory providers, allowing you to choose between different memory backends without changing application code.

## Available Providers

| Provider | Backend | Persistence | Requirements |
|----------|---------|-------------|--------------|
| `in-house` (default) | ChromaDB / Qdrant | Local disk | None (built-in) |
| `mem0` | Mem0 + Ollama + ChromaDB | In-memory only* | `pip install mem0ai`, Ollama running |
| `zep` | Zep Cloud graph API | Server-side | `pip install zep-cloud==2.0.0`, Zep API key |

\* Mem0's ChromaDB adapter uses a deprecated API that doesn't persist across restarts.

## Quick Start

### 1. Choose a provider

Edit `aios/config/config.yaml`:

```yaml
memory:
  provider: "in-house"  # or "mem0" or "zep"
```

### 2. Install dependencies (if needed)

```bash
# For Mem0
pip install mem0ai
ollama pull nomic-embed-text

# For Zep Cloud
pip install zep-cloud==2.0.0
```

### 3. Start AIOS

```bash
python -m runtime.launch
```

## Configuration

### InHouse (default)

No additional configuration needed. Uses the `storage` section in config.yaml:

```yaml
memory:
  provider: "in-house"

storage:
  vector_db_backend: "chroma"  # or "qdrant"
```

### Mem0

Requires Ollama running locally with an LLM and embedding model:

```yaml
memory:
  provider: "mem0"
  mem0:
    user_id: "default"
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
        collection_name: "mem0_memories"
```

Prerequisites:
- Ollama running at `localhost:11434`
- Models pulled: `ollama pull qwen2.5:7b` and `ollama pull nomic-embed-text`

### Zep

Requires a Zep Cloud API key (free tier works):

```yaml
memory:
  provider: "zep"
  zep:
    api_key: "your-zep-api-key"
    session_id: "default"
```

Get an API key at [app.getzep.com](https://app.getzep.com).

Note: The Zep provider uses the graph API (free tier). The sessions/memory API requires a paid plan.

## Switching Providers at Runtime

You can switch providers without restarting AIOS:

1. Edit `config.yaml` to change `memory.provider`
2. Call the refresh endpoint:
```bash
curl -X POST http://localhost:8000/core/refresh
```

## Testing Memory via API

Store a memory:
```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{
    "agent_name": "test_agent",
    "query_type": "memory",
    "query_data": {
      "operation_type": "add_memory",
      "params": {
        "content": "The user prefers Python.",
        "tags": ["preferences"],
        "category": "User Preferences"
      }
    }
  }'
```

Search memories:
```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{
    "agent_name": "test_agent",
    "query_type": "memory",
    "query_data": {
      "operation_type": "retrieve_memory",
      "params": {
        "content": "programming language preference",
        "k": 3
      }
    }
  }'
```

## Running Provider Tests

Each provider has a standalone test script in `tests/modules/memory/`:

```bash
# Test Mem0 (requires Ollama + nomic-embed-text, config set to mem0)
python tests/modules/memory/test_mem0_provider.py

# Test Zep (requires Zep API key, config set to zep)
python tests/modules/memory/test_zep_provider.py
```

Tests run directly against the provider layer without needing the full AIOS
server. Each script includes preflight checks that verify prerequisites before
running.

## Architecture

```
MemoryManager
     |
ProviderFactory
     |
  +--+--+--+
  |  |  |  |
InHouse Mem0 Zep  (your custom provider)
  |     |    |
ChromaDB Ollama+ChromaDB  Zep Cloud Graph API
```

All providers implement the `MemoryProvider` abstract base class
(`aios/memory/providers/base.py`) with six required methods:

- `add_memory(memory_note)` — store a memory
- `get_memory(memory_id)` — retrieve by ID
- `retrieve_memory(query)` — semantic search
- `update_memory(memory_note)` — update existing memory
- `retrieve_memory_raw(query)` — search returning raw MemoryNote objects
- `remove_memory(memory_id)` — delete a memory

## Adding a Custom Provider

1. Create `aios/memory/providers/my_provider.py` implementing `MemoryProvider`
2. Register it in `aios/memory/providers/factory.py`
3. Export it in `aios/memory/providers/__init__.py`
4. Add config section under `memory.my_provider` in `config.yaml`

See the steering doc at `.kiro/steering/memory-providers.md` for detailed
implementation examples.

## Provider-Specific Behavior

### Mem0
- Stores raw text and retrieves it as-is
- Semantic search via embeddings (nomic-embed-text)
- In-memory only — data lost on restart (upstream ChromaDB adapter limitation)

### Zep
- Automatically extracts structured facts from stored text
  (e.g., "The user prefers Python over JavaScript" becomes separate graph edges)
- Graph extraction is async — allow 2-8 seconds after storing before searching
- `remove_memory` is a soft no-op on the free tier (no delete endpoint)
- Data persists server-side (Zep Cloud)

## Known Issues

| Issue | Provider | Status |
|-------|----------|--------|
| No persistence across restarts | Mem0 | Upstream — Mem0 uses deprecated `chromadb.Client()` |
| No delete API on free tier | Zep | By design — `remove_memory` returns success as no-op |
| SDK version pinned to 2.0.0 | Zep | Newer versions incompatible with free tier endpoints |
| `protobuf` must be < 6.0 | Mem0 | `qdrant-client` dependency needs `protobuf 5.x` |
