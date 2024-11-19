import warnings
from dotenv import load_dotenv

from aios.sdk import FrameworkType
from aios.sdk.adapter import prepare_framework
from aios.hooks.starter import aios_starter
from aios.utils.utils import (
    parse_global_args,
    delete_directories
)
from interpreter import interpreter


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
        prepare_framework(FrameworkType.OpenInterpreter)

        # interpreter.chat("Calculate 10 * 20 / 2") interpreter.chat("Plot the sin function") interpreter.chat("Use
        # the Euclidean algorithm to calculate the greatest common divisor (GCD) of 78782 and 64.")
        interpreter.chat("In a group of 23 people, the probability of at least two having the same birthday is greater "
                         "than 50%")

    clean_cache(root_directory="./")


if __name__ == "__main__":
    main()
