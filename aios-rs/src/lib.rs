//! aios-rs: Experimental Rust rewrite scaffold of the AIOS framework.
//!
//! This crate currently provides trait definitions and minimal placeholder
//! implementations mirroring the Python architecture (context, memory,
//! scheduler, storage, tool, llm adapter). The goal is to iteratively port
//! functionality while keeping a clear boundary for mixed-language operation.
//!
//! Roadmap (high-level):
//! 1. Define core traits (done in this scaffold)
//! 2. Implement in-memory versions + simple examples
//! 3. Provide FFI / IPC bridge (e.g., via pyo3 or JSON-RPC) to allow gradual
//!    replacement of Python components
//! 4. Optimize concurrency (Tokio) and memory management
//! 5. Add feature flags for optional subsystems (vector db, scheduler variants)
//!
//! The code here is intentionally minimal; it is a foundation for further PRs.

pub mod context;
pub mod memory;
pub mod scheduler;
pub mod storage;
pub mod tool;
pub mod llm;
pub mod prelude;

// Re-export common traits for ergonomics.
pub use context::ContextManager;
pub use memory::{MemoryManager, MemoryNote, MemoryQuery, MemoryResponse};
pub use scheduler::Scheduler;
pub use storage::StorageManager;
pub use tool::ToolManager;
pub use llm::{LLMAdapter, LLMRequest, LLMResponse};

/// Version of the Rust rewrite scaffold (distinct from crate version if needed)
pub const AIOS_RS_SCAFFOLD_VERSION: &str = "0.0.1-alpha";

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn version_constant_present() {
        assert_eq!(AIOS_RS_SCAFFOLD_VERSION, "0.0.1-alpha");
    }
}
