import argparse

from aios.utils.utils import parse_global_args


def get_args():
    parser = parse_global_args()

    main_parser = argparse.ArgumentParser()
    main_parser.add_argument("--agent_type", type=str, default="interpreter")
    main_parser.add_argument("--data_name", type=str, default="gaia-benchmark/GAIA")
    main_parser.add_argument("--split", type=str, default="test")
    main_parser.add_argument("--output_file", type=str, default="prediction.json")
    main_parser.add_argument("--on_aios", action="store_true")
    main_parser.add_argument("--max_num", type=int, default=None)

    global_args, remaining_args = parser.parse_known_args()
    main_args = main_parser.parse_args(remaining_args)

    return main_args, global_args
