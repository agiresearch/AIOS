python -m experiment.humaneval.inference \
  --data_name openai/openai_humaneval \
  --split test \
  --output_file experiment/humaneval/autogen_prediction.json \
  --on_aios \
  --agent_type autogen \
  --llm_name gpt-4o-mini \
  --max_new_tokens 8000