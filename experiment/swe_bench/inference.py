import json
import re
from json import JSONDecodeError
from typing import List

from datasets import load_dataset

from aios.hooks.starter import aios_starter
from experiment.agent.experiment_agent import ExpirementAgent
from experiment.experiment_core import MetaData, AGENT_TYPE_MAPPING_AIOS, logger, run_inference
from experiment.utils import get_args


def parse_patch(agent_result: str):
    patterns = [r'```patch\s*([\s\S]*?)```', r'```diff\s*([\s\S]*?)```', r'<patch>(.*?)</patch>']

    for pattern in patterns:
        match = re.search(pattern, agent_result)
        if match:
            patch = match.group(1)
            return patch

    try:
        with open("wrong_result.json", "r", encoding="utf-8") as file:
            predictions = json.load(file)
    except FileNotFoundError:
        predictions = []
    except JSONDecodeError:
        predictions = []

    predictions.append(agent_result)
    with open("wrong_result.json", "w", encoding="utf-8") as file:
        json.dump(predictions, file, ensure_ascii=False, indent=4)

    return "[None]"


def write_prediction(instance_id: str, model_patch: str, model_name_or_path: str, out_path: str):
    prediction = {
        "instance_id": instance_id,
        "model_patch": model_patch,
        "model_name_or_path": model_name_or_path,
    }

    try:
        with open(out_path, "r", encoding="utf-8") as file:
            predictions = json.load(file)
    except FileNotFoundError:
        predictions = []
    except JSONDecodeError:
        predictions = []

    predictions.append(prediction)

    with open(out_path, "w", encoding="utf-8") as file:
        json.dump(predictions, file, ensure_ascii=False, indent=4)

    print(f"Write prediction: {prediction}")


def write_output_func(result_list: List, output_file: str):
    with open(output_file, "w", encoding="utf-8") as file:
        json.dump(result_list, file, ensure_ascii=False, indent=4)
    logger.log(f"Write results num: {len(result_list)}", level="info")


def process_one_func(data, meta_data: MetaData):
    if meta_data.on_aios:
        with aios_starter(**meta_data.aios_args):
            agent: ExpirementAgent = AGENT_TYPE_MAPPING_AIOS[meta_data.agent_type](meta_data.on_aios)
            input_str = data["text"]
            result = agent.run(input_str)
            patch = parse_patch(result)

            prediction = {
                "instance_id": data["instance_id"],
                "model_patch": patch,
                "model_name_or_path": meta_data.agent_type,
            }
        return prediction
    else:
        agent: ExpirementAgent = AGENT_TYPE_MAPPING_AIOS[meta_data.agent_type](meta_data.on_aios)
        input_str = data["text"]
        result = agent.run(input_str)
        patch = parse_patch(result)

        prediction = {
            "instance_id": data["instance_id"],
            "model_patch": patch,
            "model_name_or_path": meta_data.agent_type,
        }
        return prediction


if __name__ == '__main__':
    main_args, global_args = get_args()

    agent_type = "swe:" + main_args.agent_type
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
        write_output_func=write_output_func
    )
