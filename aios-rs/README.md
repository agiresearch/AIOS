# aios-rs

Experimental Rust rewrite scaffold of the AIOS framework. This is an early foundation providing core trait definitions and minimal reference implementations so that the Python system can be incrementally ported / inter-operated.

## Status
- Traits defined: context, memory, storage, tool, scheduler, llm adapter
- Minimal in-memory / filesystem / echo implementations
- No async runtime yet (Tokio not added)
- No vector DB / embedding integration yet
- No FFI bridge to Python yet

## Goals (incremental roadmap)
1. Flesh out trait contracts (streaming, structured errors, async)
2. Provide concrete async implementations (Tokio + channels)
3. Add vector store abstraction + pluggable backends
4. Introduce pyo3 / JSON-RPC bridge for hybrid operation
5. Port scheduling strategies (FIFO, RR) with test parity
6. Add feature flags: `vector`, `python-bridge`, `tokio-scheduler`
7. Performance + memory benchmarks

## Quick Start
```bash
# In repository root
cd aios-rs
cargo test
```

Add to another crate (path dependency while developing):
```toml
[dependencies]
aios-rs = { path = "../aios-rs" }
```

Example usage:
```rust
use aios_rs::prelude::*;

fn main() -> anyhow::Result<()> {
    let llm = std::sync::Arc::new(EchoLLM);
    let memory = std::sync::Arc::new(std::sync::Mutex::new(InMemoryMemoryManager::new()));
    let storage = std::sync::Arc::new(FsStorageManager::new("/tmp/aios_store"));
    let tool = std::sync::Arc::new(NoopToolManager);
    let mut scheduler = NoopScheduler::new(llm, memory, storage, tool);
    scheduler.start()?;
    scheduler.stop()?;
    Ok(())
}
```

## Contributing
This scaffold intentionally keeps scope narrow; please open an issue or discussion before expanding new subsystems. Focus areas welcome: async design, error model, bridging strategy, test parity with Python.

## License
Apache-2.0
