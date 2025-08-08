//! Storage manager trait (placeholder) analogous to Python storage subsystem.
use std::path::PathBuf;

pub trait StorageManager: Send + Sync {
    fn put(&self, key: &str, data: &[u8]) -> anyhow::Result<()>;
    fn get(&self, key: &str) -> anyhow::Result<Option<Vec<u8>>>;
}

pub struct FsStorageManager { root: PathBuf }
impl FsStorageManager { pub fn new(root: impl Into<PathBuf>) -> Self { Self { root: root.into() } } }

impl StorageManager for FsStorageManager {
    fn put(&self, key: &str, data: &[u8]) -> anyhow::Result<()> {
        let path = self.root.join(key);
        if let Some(parent) = path.parent() { std::fs::create_dir_all(parent)?; }
        std::fs::write(path, data)?;
        Ok(())
    }
    fn get(&self, key: &str) -> anyhow::Result<Option<Vec<u8>>> {
        let path = self.root.join(key);
        if path.exists() { Ok(Some(std::fs::read(path)?)) } else { Ok(None) }
    }
}
