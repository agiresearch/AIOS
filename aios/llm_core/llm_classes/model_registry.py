# registering all proprietary llm models in a constant

from .gpt_llm import GPTLLM
from .gemini_llm import GeminiLLM
from .bed_rock import BedrockLLM
from .claude_llm import ClaudeLLM

#used for closed LLM model registry
MODEL_REGISTRY = {
    'bedrock/anthropic.claude-3-haiku-20240307-v1:0': BedrockLLM,
    'gemini-1.0-pro': GeminiLLM,
    "gemini-1.0-pro-001": GeminiLLM,
    "gemini-1.5-flash-latest": GeminiLLM,
    "gemini-1.5-pro-latest": GeminiLLM,
    'gpt-3.5-turbo': GPTLLM,
    'gpt-4': GPTLLM,
    'gpt-4o': GPTLLM,
    'claude-3-5-sonnet-20240620': ClaudeLLM
}
