# registering all proprietary llm models in a constant

from .gpt_llm import GPTLLM
from .gemini_llm import GeminiLLM
from .bed_rock import BedrockLLM
from .claude_llm import ClaudeLLM
from .groq_llm import GroqLLM

#used for closed LLM model registry
MODEL_REGISTRY = {
    # Gemini-1.5
    "gemini-1.5-flash": GeminiLLM,
    "gemini-1.5-pro": GeminiLLM,

    # GPT3.5
    'gpt-3.5-turbo': GPTLLM,
    'gpt-4-turbo': GPTLLM,

    # GPT4o
    'gpt-4o': GPTLLM,
    'gpt-4o-2024-05-13': GPTLLM,
    'gpt-4o-mini': GPTLLM,

    # claude
    'claude-3-5-sonnet-20240620': ClaudeLLM,
    'bedrock/anthropic.claude-3-haiku-20240307-v1:0': BedrockLLM,

    #Groq
    'llama3-groq-8b-8192-tool-use-preview': GroqLLM,
    'llama3-70b-8192': GroqLLM,
    'mixtral-8x7b-32768' : GroqLLM
}
