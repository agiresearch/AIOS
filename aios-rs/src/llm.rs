//! LLM adapter trait and simple echo implementation.
use anyhow::Result;

pub trait LLMAdapter: Send + Sync {
    fn infer(&self, request: LLMRequest) -> Result<LLMResponse>;
}

#[derive(Debug, Clone)]
pub struct LLMRequest { pub prompt: String }
#[derive(Debug, Clone)]
pub struct LLMResponse { pub content: String }

pub struct EchoLLM;
impl LLMAdapter for EchoLLM {
    fn infer(&self, request: LLMRequest) -> Result<LLMResponse> {
        Ok(LLMResponse { content: format!("echo: {}", request.prompt) })
    }
}
