import argparse
import json

from datasets import load_dataset
from tqdm import tqdm

from experiment.experiment_core import logger


def run_evaluation(input_file: str, output_file: str, data_name: str, split: str):
    dataset = load_dataset(data_name, "2023_all", split=split)

    with open(input_file, "r", encoding="utf-8") as file:
        predictions = json.load(file)

    right_num = 0
    error_predictions = []
    for prediction, data in tqdm(zip(predictions, dataset)):
        if prediction["result"] == data["Final answer"]:
            right_num += 1
        else:
            error_predictions.append({
                "task_id": data["task_id"],
                "error_answer": prediction["result"],
                "right_answer": data["Final answer"],
            })

    with open(output_file, "w", encoding="utf-8") as file:
        json.dump(error_predictions, file, ensure_ascii=False, indent=4)

    logger.log(f"Total num: {len(predictions)} \n"
               f"             Right num: {right_num} \n"
               f"             Right Rate: {right_num/len(predictions)}"
               , level="info")


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--input_file", type=str, default="experiment/gaia_prediction.json")
    parser.add_argument("--output_file", type=str, default="experiment/gaia_evaluation.json")
    parser.add_argument("--data_name", type=str, default="gaia-benchmark/GAIA")
    parser.add_argument("--split", type=str, default="validation")

    args = parser.parse_args()
    run_evaluation(
        args.input_file,
        args.output_file,
        args.data_name,
        args.split
    )
