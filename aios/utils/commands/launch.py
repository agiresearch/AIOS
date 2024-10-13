from aios.utils.utils import parse_global_args


def main():
    parser = parse_global_args()
    args = parser.parse_args()

    print("Welcome to AIOS!")
    print(f"Args: {vars(args)}")
