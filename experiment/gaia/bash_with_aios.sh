python -m experiment.gaia.inference \
  --data_name gaia-benchmark/GAIA \
  --split validation \
  --output_file experiment/gaia_prediction.json \
  --on_aios \
  --agent_type autogen \
  --llm_name gpt-4o-mini \
  --max_new_tokens 8000