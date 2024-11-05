from aios.hooks.llm import aios_starter
from aios.utils.utils import parse_global_args
from pyopenagi.agents.experiment.standard.agent import StandardAgent


def process_one_func(input_str: str):
    agent = StandardAgent("Standard Agent", input_str)
    result = agent.run()
    print(result)


def run_infer(aios_args: dict):

    with aios_starter(*aios_args):
        process_one_func("")


if __name__ == '__main__':
    parser = parse_global_args()

    args = parser.parse_args()
    aios_args = {
        "llm_name": args.llm_name,
        "max_gpu_memory": args.max_gpu_memory,
        "eval_device": args.eval_device,
        "max_new_tokens": args.max_new_tokens,
        "log_mode": args.log_mode,
        "use_backend": args.use_backend,
    }
