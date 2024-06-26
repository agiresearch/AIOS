# registering all proprietary llm models in a constant

from .gpt_llm import GPTLLM
from .gemini_llm import GeminiLLM
from .bed_rock import BedrockLLM

#used for closed LLM model registry
MODEL_REGISTRY = {
    'bedrock/anthropic.claude-3-haiku-20240307-v1:0': BedrockLLM,
    'gemini-pro': GeminiLLM,
    'gpt-3.5-turbo': GPTLLM,
    'gpt-4': GPTLLM,
    'gpt-4o': GPTLLM
}
