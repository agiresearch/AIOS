run-agent \
    --llm_name llama3:8b \
    --llm_backend ollama \
    --agent_name_or_path demo_author/demo_agent \
    --task "Tell me what is core idea of AIOS" \
    --aios_kernel_url http://localhost:8000

run-agent \
    --llm_name gpt-4o-mini \
    --llm_backend openai \
    --agent_name_or_path demo_author/demo_agent \
    --task "Tell me what is core idea of AIOS" \
    --aios_kernel_url http://localhost:8000