from aios.llm_core.cores.api.google import GeminiLLM
from aios.llm_core.cores.api.openai import GPTLLM
from aios.llm_core.cores.api.anthropic import ClaudeLLM

MODEL_REGISTRY = {
    # Gemini
    "gemini-1.5-flash": GeminiLLM,
    "gemini-1.5-pro": GeminiLLM,

    # GPT
    'gpt-3.5-turbo': GPTLLM,
    'gpt-4-turbo': GPTLLM,
    'gpt-4o': GPTLLM,
    'gpt-4o-2024-05-13': GPTLLM,
    'gpt-4o-mini': GPTLLM,
    
    # Claude
    'claude-3-5-sonnet-latest': ClaudeLLM,
    'claude-3-5-haiku-latest': ClaudeLLM,
    'claude-3-opus-latest': ClaudeLLM
}