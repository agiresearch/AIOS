# registering all proprietary llm models in a constant



#used for closed LLM model registry
from cerebrum.llm.providers.api.anthropic import ClaudeLLM
from cerebrum.llm.providers.api.google import GeminiLLM
from cerebrum.llm.providers.api.openai import GPTLLM


API_MODEL_REGISTRY = {
    # Gemini
    "gemini-1.5-flash": GeminiLLM,
    "gemini-1.5-pro": GeminiLLM,

    # GPT
    'gpt-3.5-turbo': GPTLLM,
    'gpt-4-turbo': GPTLLM,
    'gpt-4o': GPTLLM,
    'gpt-4o-2024-05-13': GPTLLM,
    'gpt-4o-mini': GPTLLM,

    # claude
    'claude-3-5-sonnet-20240620': ClaudeLLM,

    # amazon bedrock
    # 'bedrock/anthropic.claude-3-haiku-20240307-v1:0': BedrockLLM,

    #Groq
    # 'llama3-groq-8b-8192-tool-use-preview': GroqLLM,
    # 'llama3-70b-8192': GroqLLM,
    # 'mixtral-8x7b-32768' : GroqLLM
}
