python -m experiment.humaneval.inference \
  --data_name openai/openai_humaneval \
  --split test \
  --output_file experiment/swe_bench/eval_prediction.json \
  --on_aios \
  --agent_type interpreter \
  --llm_name gpt-4o-mini \
  --max_new_tokens 8000