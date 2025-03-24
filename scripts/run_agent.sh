# run agent with gemini-1.5-flash
run-agent \
    --llm_name gemini-1.5-flash \
    --llm_backend google \
    --agent_name_or_path demo_author/demo_agent \
    --task "Tell me what is core idea of AIOS" \
    --aios_kernel_url http://localhost:8000

# run agent with gpt-4o-mini using openai
run-agent \
    --llm_name gpt-4o-mini \
    --llm_backend openai \
    --agent_name_or_path demo_author/demo_agent \
    --task "Tell me what is core idea of AIOS" \
    --aios_kernel_url http://localhost:8000

# run agent with gpt-4o-mini using openai
vllm serve meta-llama/Meta-Llama-3-8B-Instruct --dtype auto --port 8001 # start the vllm server
run-agent \
    --llm_name meta-llama/Meta-Llama-3-8B-Instruct \
    --llm_backend vllm \
    --agent_name_or_path demo_author/demo_agent \
    --task "Tell me what is core idea of AIOS" \
    --aios_kernel_url http://localhost:8000

# run agent with llama3:8b using ollama
ollama pull llama3:8b # pull the model
ollama serve # start the ollama server
run-agent \
    --llm_name llama3:8b \
    --llm_backend ollama \
    --agent_name_or_path demo_author/demo_agent \
    --task "Tell me what is core idea of AIOS" \
    --aios_kernel_url http://localhost:8000


curl -X POST http://localhost:8000/agents/submit \
    -H "Content-Type: application/json" \
    -d '{
        "agent_id": "example/academic_agent",
        "agent_config": {
            "task": "Tell me what is core idea of AIOS"
        }
    }'

# curl -X GET http://localhost:8000/agents/225269/status

curl -X POST http://localhost:8000/core/refresh

# curl -X POST http://localhost:8000/core/cleanup

