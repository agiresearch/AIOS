## run inference
```shell
python -m experiment.humaneval.inference \
  --data_name openai/openai_humaneval \
  --split test \
  --output_file experiment/humaneval_prediction.json \
  --on_aios \
#  --max_num 1 \
  --agent_type interpreter \
  --llm_name gpt-4o-mini \
  --max_new_tokens 8000
```
