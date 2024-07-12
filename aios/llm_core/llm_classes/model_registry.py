# registering all proprietary llm models in a constant

from .gpt_llm import GPTLLM
from .gemini_llm import GeminiLLM
from .bed_rock import BedrockLLM
from .claude_llm import ClaudeLLM

#used for closed LLM model registry
MODEL_REGISTRY = {
    'bedrock/anthropic.claude-3-haiku-20240307-v1:0': BedrockLLM,
    # Gemini-1.0
    'gemini-1.0-pro': GeminiLLM,
    "gemini-1.0-pro-001": GeminiLLM,

    # Gemini-1.5
    "gemini-1.5-flash": GeminiLLM,
    "gemini-1.5-pro": GeminiLLM,

    # GPT3.5
    'gpt-3.5-turbo': GPTLLM,
    'gpt-4-turbo': GPTLLM,

    # GPT4
    'gpt-4-turbo-2024-04-09': GPTLLM,
    'gpt-4-turbo-preview': GPTLLM,
    'gpt-4-0125-preview': GPTLLM,
    'gpt-4': GPTLLM,
  
    # GPT4o
    'gpt-4o': GPTLLM,
    'gpt-4o-2024-05-13': GPTLLM,
  
    # claude 
    'claude-3-5-sonnet-20240620': ClaudeLLM
}
