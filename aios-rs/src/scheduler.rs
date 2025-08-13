//! Scheduler trait (simplified placeholder).
use crate::{LLMAdapter, MemoryManager, StorageManager, ToolManager};
use std::sync::Arc;

pub trait Scheduler: Send + Sync {
    fn start(&mut self) -> anyhow::Result<()>;
    fn stop(&mut self) -> anyhow::Result<()>;
}

pub struct NoopScheduler {
    pub llm: Arc<dyn LLMAdapter>,
    pub memory: Arc<std::sync::Mutex<dyn MemoryManager>>,
    pub storage: Arc<dyn StorageManager>,
    pub tool: Arc<dyn ToolManager>,
    running: bool,
}

impl NoopScheduler {
    pub fn new(
        llm: Arc<dyn LLMAdapter>,
        memory: Arc<std::sync::Mutex<dyn MemoryManager>>,
        storage: Arc<dyn StorageManager>,
        tool: Arc<dyn ToolManager>,
    ) -> Self { Self { llm, memory, storage, tool, running: false } }
}

impl Scheduler for NoopScheduler {
    fn start(&mut self) -> anyhow::Result<()> { self.running = true; Ok(()) }
    fn stop(&mut self) -> anyhow::Result<()> { self.running = false; Ok(()) }
}
