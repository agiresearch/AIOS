//! Memory subsystem mirroring Python base memory manager (simplified).
use std::collections::HashMap;
use std::time::{SystemTime, UNIX_EPOCH};

#[derive(Debug, Clone)]
pub struct MemoryNote {
    pub id: String,
    pub content: String,
    pub keywords: Vec<String>,
    pub tags: Vec<String>,
    pub category: Option<String>,
    pub timestamp: u64,
}

impl MemoryNote {
    pub fn new(id: impl Into<String>, content: impl Into<String>) -> Self {
        Self {
            id: id.into(),
            content: content.into(),
            keywords: vec![],
            tags: vec![],
            category: None,
            timestamp: SystemTime::now()
                .duration_since(UNIX_EPOCH)
                .unwrap()
                .as_secs(),
        }
    }
}

#[derive(Debug, Clone)]
pub struct MemoryQuery {
    pub operation: String,
    pub params: HashMap<String, String>,
}

#[derive(Debug, Clone)]
pub struct MemoryResponse {
    pub success: bool,
    pub memory_id: Option<String>,
    pub content: Option<String>,
    pub error: Option<String>,
}

impl MemoryResponse {
    pub fn ok_id(id: impl Into<String>) -> Self { Self { success: true, memory_id: Some(id.into()), content: None, error: None } }
    pub fn ok_content(content: impl Into<String>) -> Self { Self { success: true, memory_id: None, content: Some(content.into()), error: None } }
    pub fn err(e: impl Into<String>) -> Self { Self { success: false, memory_id: None, content: None, error: Some(e.into()) } }
}

pub trait MemoryManager: Send + Sync {
    fn add_memory(&mut self, note: MemoryNote) -> MemoryResponse;
    fn remove_memory(&mut self, id: &str) -> MemoryResponse;
    fn update_memory(&mut self, note: MemoryNote) -> MemoryResponse;
    fn get_memory(&self, id: &str) -> MemoryResponse;
}

pub struct InMemoryMemoryManager {
    notes: HashMap<String, MemoryNote>,
}

impl InMemoryMemoryManager { pub fn new() -> Self { Self { notes: HashMap::new() } } }

impl MemoryManager for InMemoryMemoryManager {
    fn add_memory(&mut self, note: MemoryNote) -> MemoryResponse {
        let id = note.id.clone();
        self.notes.insert(id.clone(), note);
        MemoryResponse::ok_id(id)
    }
    fn remove_memory(&mut self, id: &str) -> MemoryResponse {
        if self.notes.remove(id).is_some() { MemoryResponse::ok_id(id) } else { MemoryResponse::err("not found") }
    }
    fn update_memory(&mut self, note: MemoryNote) -> MemoryResponse {
        let id = note.id.clone();
        if self.notes.contains_key(&id) {
            self.notes.insert(id.clone(), note);
            MemoryResponse::ok_id(id)
        } else { MemoryResponse::err("not found") }
    }
    fn get_memory(&self, id: &str) -> MemoryResponse {
        self.notes.get(id).map(|n| MemoryResponse::ok_content(n.content.clone())).unwrap_or_else(|| MemoryResponse::err("not found"))
    }
}
