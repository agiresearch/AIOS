import argparse

def parse_global_args():
    parser = argparse.ArgumentParser(description="Parse global parameters")
    parser.add_argument('--llm_name', type=str, default="gemma-2b-it")
    
    return parser