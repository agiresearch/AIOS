//! Context subsystem (snapshot + recovery) trait definitions.
use std::path::PathBuf;

pub trait ContextManager: Send + Sync {
    fn start(&mut self) -> anyhow::Result<()> { Ok(()) }
    fn gen_snapshot(&self, pid: u64, context: &str) -> anyhow::Result<PathBuf>;
    fn gen_recover(&self, pid: u64) -> anyhow::Result<Option<String>>;
    fn stop(&mut self) -> anyhow::Result<()> { Ok(()) }
}

/// A minimal in-memory context manager placeholder.
pub struct InMemoryContextManager {
    root: PathBuf,
}

impl InMemoryContextManager {
    pub fn new(root: impl Into<PathBuf>) -> Self { Self { root: root.into() } }
}

impl ContextManager for InMemoryContextManager {
    fn gen_snapshot(&self, pid: u64, context: &str) -> anyhow::Result<PathBuf> {
        let file = self.root.join(format!("ctx_{pid}.txt"));
        std::fs::create_dir_all(&self.root)?;
        std::fs::write(&file, context)?;
        Ok(file)
    }
    fn gen_recover(&self, pid: u64) -> anyhow::Result<Option<String>> {
        let file = self.root.join(format!("ctx_{pid}.txt"));
        if file.exists() { Ok(Some(std::fs::read_to_string(file)?)) } else { Ok(None) }
    }
}
