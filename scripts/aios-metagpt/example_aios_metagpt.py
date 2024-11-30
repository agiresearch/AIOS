import warnings
from dotenv import load_dotenv
from aios.hooks.llm import aios_starter
from aios.sdk import prepare_framework, FrameworkType
from aios.utils.utils import (
    parse_global_args,
    delete_directories
)
from metagpt.software_company import generate_repo, ProjectRepo


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
        repo: ProjectRepo = generate_repo("Create a 2048 game")  # or ProjectRepo("<path>")
        print(repo)

    clean_cache(root_directory="./")


if __name__ == "__main__":
    main()
