import json
from argparse import ArgumentParser
from experiment.benchmark.gaia.run_infer import prepare_dataset


def run_eval(input_file: str, output_file: str):
    dataset = prepare_dataset()
    dataset_map = {data["task_id"]: data for data in dataset}
    with open(input_file, "r", encoding="utf-8") as file:
        predictions = [json.loads(line) for line in file]

    pass_num = 0
    for prediction in predictions:
        task_id = prediction["task_id"]
        result = prediction["result"]
        true_result = dataset_map[task_id]["Final answer"]
        if result == true_result:
            prediction["pass"] = True
            pass_num += 1
        else:
            prediction["pass"] = False
            prediction["true_result"] = true_result

    with open(output_file, "w") as file:
        for line in predictions:
            json_line = json.dumps(line)
            file.write(json_line + "\n")

    print(f"Gaia passed: {pass_num}, total: {len(predictions)}, pass rate: {pass_num/len(predictions)}")


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument("--input_file", type=str, default="./experiment/benchmark/gaia/predictions.jsonl")
    parser.add_argument("--output_file", type=str, default="./experiment/benchmark/gaia/report.jsonl")
    args = parser.parse_args()
    run_eval(args.input_file, args.output_file)
