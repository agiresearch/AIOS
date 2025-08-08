//! Tool subsystem placeholder.
use anyhow::Result;

pub trait ToolManager: Send + Sync {
    fn invoke(&self, name: &str, input: &str) -> Result<String>;
}

pub struct NoopToolManager;
impl ToolManager for NoopToolManager {
    fn invoke(&self, name: &str, input: &str) -> Result<String> {
        Ok(format!("tool:{name} echo -> {input}"))
    }
}
