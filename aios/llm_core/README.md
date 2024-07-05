# aios/llm_core/

This directory contains wrapper classes that abstract the LLMs into a single class called LLMKernel. Currently, the following models are supported:

1. GPT
2. ollama
3. Gemini
4. Claude
5. huggingface open source models

In the future, greedy token generation and lm types other than casual will be supported.
