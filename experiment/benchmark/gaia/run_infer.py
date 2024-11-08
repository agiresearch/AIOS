import json
import os
from concurrent.futures import ThreadPoolExecutor, as_completed

from tqdm import tqdm

from aios.hooks.llm import aios_starter
from aios.utils.utils import parse_global_args
from pyopenagi.agents.experiment.standard.agent import StandardAgent

DATA_PATH = os.path.join(
    os.path.dirname(os.path.realpath(__file__)),
    "gaia",
    "2023",
    "validation"
)

SYSTEM_PROMPT = """You are a general AI assistant. I will ask you a question. Report your thoughts, and finish
your answer with the following template: FINAL ANSWER: [YOUR FINAL ANSWER].
YOUR FINAL ANSWER should be a number OR as few words as possible OR a comma separated list of
numbers and/or strings.
If you are asked for a number, don’t use comma to write your number neither use units such as $ or percent
sign unless specified otherwise.
If you are asked for a string, don’t use articles, neither abbreviations (e.g. for cities), and write the digits in
plain text unless specified otherwise.
If you are asked for a comma separated list, apply the above rules depending of whether the element to be put
in the list is a number or a string."""


def process_one_func(data):
    agent = StandardAgent("Standard Agent", data["Question"])
    agent.custom_prompt = lambda: SYSTEM_PROMPT
    result = agent.run()
    print(result)
    return {
        "task_id": 1,
        "result": data["Question"]
    }


def prepare_dataset():
    input_file = os.path.join(DATA_PATH, "metadata.jsonl")
    with open(input_file, "r") as file:
        dataset = [json.loads(line) for line in file]

    return dataset


def run_infer(outputfile: str, workers: int, aios_args: dict):
    dataset = prepare_dataset()
    with aios_starter(**aios_args):
        with ThreadPoolExecutor(max_workers=workers) as executor:

            futures = []
            for data in dataset:
                # 提交任务
                futures.append(
                    executor.submit(process_one_func, data)
                )
                break

        results = []

        # Obtain infer result
        for future in tqdm(as_completed(futures)):
            results.append(future.result())

    # Write result into .jsonl file
    with open(outputfile, "w") as file:
        for line in results:
            json_line = json.dumps(line)
            file.write(json_line + "\n")


if __name__ == '__main__':
    parser = parse_global_args()
    parser.add_argument("--output_file", type=str, default="./experiment/benchmark/gaia/predictions.jsonl")
    parser.add_argument("--workers", type=int, default=1)

    args = parser.parse_args()
    aios_args = {
        "llm_name": args.llm_name,
        "max_gpu_memory": args.max_gpu_memory,
        "eval_device": args.eval_device,
        "max_new_tokens": args.max_new_tokens,
        "scheduler_log_mode": args.scheduler_log_mode,
        "agent_log_mode": args.agent_log_mode,
        "llm_kernel_log_mode": args.llm_kernel_log_mode,
        "use_backend": args.use_backend,
    }

    run_infer(
        args.output_file,
        args.workers,
        aios_args
    )
