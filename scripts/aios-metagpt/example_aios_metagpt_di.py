import warnings

from aios.sdk import FrameworkType, prepare_framework
from dotenv import load_dotenv
from aios.hooks.llm import aios_starter
from aios.utils.utils import (
    parse_global_args,
    delete_directories
)
import asyncio
from metagpt.roles.di.data_interpreter import DataInterpreter


def clean_cache(root_directory):
    targets = {
        ".ipynb_checkpoints",
        "__pycache__",
        ".pytest_cache",
        "context_restoration",
    }
    delete_directories(root_directory, targets)


def main():
    # parse arguments and set configuration for this run accordingly
    warnings.filterwarnings("ignore")
    parser = parse_global_args()
    args = parser.parse_args()
    load_dotenv()

    with aios_starter(**vars(args)):
        prepare_framework(FrameworkType.MetaGPT)

        async def di_main():
            di = DataInterpreter()
            await di.run("Run data analysis on sklearn Iris dataset, include a plot")

        asyncio.run(di_main())  # or await main() in a jupyter notebook setting

    clean_cache(root_directory="./")


if __name__ == "__main__":
    main()
