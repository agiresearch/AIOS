import argparse

import os
import shutil

from typing import Dict, List, Any, Optional

import json

import re

# logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
# logger = logging.getLogger(__name__)

def parse_global_args():
    parser = argparse.ArgumentParser(description="Parse global parameters")
    parser.add_argument('--llm_name', type=str, default="gemma-2b-it", help="Specify the LLM name of AIOS")
    parser.add_argument('--max_gpu_memory', type=json.loads, help="Max gpu memory allocated for the LLM")
    parser.add_argument('--eval_device', type=str, help="Evaluation device")
    parser.add_argument('--max_new_tokens', type=int, default=256, help="The maximum number of new tokens for generation")
    parser.add_argument("--scheduler_log_mode", type=str, default="console", choices=["console", "file"])
    parser.add_argument("--agent_log_mode", type=str, default="console", choices=["console", "file"])
    parser.add_argument("--llm_kernel_log_mode", type=str, default="console", choices=["console", "file"])

    return parser

def extract_before_parenthesis(s: str) -> str:
    match = re.search(r'^(.*?)\([^)]*\)', s)
    return match.group(1) if match else s

def get_from_dict_or_env(
    data: Dict[str, Any], key: str, env_key: str, default: Optional[str] = None
) -> str:
    """Get a value from a dictionary or an environment variable."""
    if key in data and data[key]:
        return data[key]
    else:
        return get_from_env(key, env_key, default=default)


def get_from_env(env_key: str, default: Optional[str] = None) -> str:
    """Get a value from an environment variable."""
    if env_key in os.environ and os.environ[env_key]:
        return os.environ[env_key]
    elif default is not None:
        return default
    else:
        raise ValueError(
            f"Did not find {env_key}, please add an environment variable"
            f" `{env_key}` which contains it. "
        )

class Logger:
    def __init__(self, log_mode) -> None:
        self.log_mode = log_mode

    def log(self, info, path=None):
        if self.log_mode == "console":
            print(info)
        else:
            assert self.log_mode == "file"
            with open(path, "w") as w:
                w.write(info + "\n")

def delete_directories(root_dir, target_dirs):
    """
    Recursively deletes directories with names in target_dirs starting from root_dir.
    """
    for dirpath, dirnames, filenames in os.walk(root_dir, topdown=False):
        for dirname in dirnames:
            if dirname in target_dirs:
                full_path = os.path.join(dirpath, dirname)
                # print(f"Deleting {full_path}...")
                shutil.rmtree(full_path, ignore_errors=True)
