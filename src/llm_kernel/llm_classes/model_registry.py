from .gpt_llm import GPTLLM
from .open_llm import OpenLLM
from .gemini_llm import GeminiLLM
from .bed_rock import BedrockLLM

#used for closed LLM model registry
MODEL_REGISTRY = {
    'bedrock/anthropic.claude-3-haiku-20240307-v1:0': BedrockLLM,
    'gemini-pro': GeminiLLM,
    'gpt-3.5-turbo': GPTLLM,
    'gpt-4': GPTLLM
}
