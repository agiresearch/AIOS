//! Convenience prelude re-exporting primary traits & structs.
pub use crate::context::{ContextManager, InMemoryContextManager};
pub use crate::memory::{MemoryManager, InMemoryMemoryManager, MemoryNote, MemoryQuery, MemoryResponse};
pub use crate::scheduler::{Scheduler, NoopScheduler};
pub use crate::storage::{StorageManager, FsStorageManager};
pub use crate::tool::{ToolManager, NoopToolManager};
pub use crate::llm::{LLMAdapter, EchoLLM, LLMRequest, LLMResponse};
