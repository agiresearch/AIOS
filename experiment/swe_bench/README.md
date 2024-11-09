# How to run SWE-Bench

## Step 0
Install SWE-Bench as following:
```shell
git clone git@github.com:princeton-nlp/SWE-bench.git
cd SWE-bench
pip install -e .
```

## Step 1
You need to run `inference.py` to get agent output.
Your agent's output needs to be in the following format.
```text
{
    "instance_id": "<Unique task instance ID>",
    "model_patch": "<.patch file content string>",
    "model_name_or_path": "<Model name here (i.e. SWE-Llama-13b)>",
}
```
Collect all agent output as a `.jsonl` or `.json` file. Like `predictions.jsonl`.

## Step 2
Run evaluation like this:
```shell
python -m pyopenagi.data.swebench.run_evaluation \
    --dataset_name princeton-nlp/SWE-bench_Lite \
    --predictions_path <path_to_predictions> \
    --max_workers <num_workers> \
    --run_id <run_id>
    # use --predictions_path 'gold' to verify the gold patches
    # use --run_id to name the evaluation run
```
`--predictions_path` is the path of your `predictions.jsonl`
