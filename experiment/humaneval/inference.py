import json
import re
from typing import List
from datasets import load_dataset
from aios.hooks.starter import aios_starter
from experiment.agent.experiment_agent import ExpirementAgent
from experiment.experiment_core import logger, MetaData, AGENT_TYPE_MAPPING_AIOS, run_inference
from experiment.utils import get_args


def parse_result(result: str):
    match = re.search(r'```python\s*([\s\S]*?)```', result)
    if match:
        result = match.group(1)

    if not result.startswith("def") or not result.startswith("import"):
        result += "    "

    code_lines = result.split("\n")
    for line in code_lines[:]:
        if line.startswith("def"):
            code_lines.remove(line)
        elif line.startswith("import"):
            line += "    "
    result = "\n".join(code_lines)

    return result


def write_output_func(result_list: List, output_file: str):
    with open(output_file, "w", encoding="utf-8") as file:
        for result in result_list:
            json_line = json.dumps(result)
            file.write(json_line + "\n")
    logger.log(f"Write results num: {len(result_list)}", level="info")


def process_one_func(data, meta_data: MetaData):
    if meta_data.on_aios:
        with aios_starter(**meta_data.aios_args):
            agent: ExpirementAgent = AGENT_TYPE_MAPPING_AIOS[meta_data.agent_type](meta_data.on_aios)
            result = agent.run(data["prompt"])
            result = parse_result(result)

            prediction = {
                "task_id": data["task_id"],
                "completion": result,
            }
            return prediction

    else:
        agent: ExpirementAgent = AGENT_TYPE_MAPPING_AIOS[meta_data.agent_type](meta_data.on_aios)
        result = agent.run(data["prompt"])
        result = parse_result(result)

        prediction = {
            "task_id": data["task_id"],
            "completion": result,
        }
        return prediction


if __name__ == '__main__':
    main_args, global_args = get_args()

    agent_type = "humaneval:" + main_args.agent_type
    dataset = load_dataset(main_args.data_name, split=main_args.split)

    meta = MetaData(
        dataset=dataset,
        agent_type=agent_type,
        output_file=main_args.output_file,
        on_aios=main_args.on_aios,
        max_num=main_args.max_num,
        aios_args=vars(global_args),
    )

    run_inference(
        meta_data=meta,
        process_one_func=process_one_func,
        write_output_func=write_output_func,
    )
