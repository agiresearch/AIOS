# This file contains helpful utilities for the rest of the code, encompassing
# parsing, environment variables, logging, etc.

# TODO: switch to click

import argparse

import os
import shutil

import json

from typing import Dict, Any, Optional

import re

# logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
# logger = logging.getLogger(__name__)

def parse_global_args():
    parser = argparse.ArgumentParser(description="Parse global parameters")
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # env command
    env_parser = subparsers.add_parser('env', help='Manage environment variables')
    env_subparsers = env_parser.add_subparsers(dest='env_command', help='Environment variable commands')
    
    # env list
    env_list_parser = env_subparsers.add_parser('list', help='List available API keys')
    
    # env set
    env_set_parser = env_subparsers.add_parser('set', help='Set an API key')
    env_set_parser.add_argument('key', nargs='?', help='API key name')
    env_set_parser.add_argument('value', nargs='?', help='API key value')
    
    # refresh command
    refresh_parser = subparsers.add_parser('refresh', help='Refresh configuration')
    
    # Global parameters
    parser.add_argument('--llm_name', type=str, default="gpt-4o-mini", help="Specify the LLM name of AIOS")
    parser.add_argument('--max_gpu_memory', type=json.loads, help="Max gpu memory allocated for the LLM")
    parser.add_argument('--eval_device', type=str, help="Evaluation device")
    parser.add_argument('--max_new_tokens', type=int, default=256, help="The maximum number of new tokens for generation")
    parser.add_argument("--scheduler_log_mode", type=str, default="console", choices=["console", "file"], help="Log mode for the scheduler")
    parser.add_argument("--agent_log_mode", type=str, default="console", choices=["console", "file"], help="Log mode for the agents")
    parser.add_argument("--llm_core_log_mode", type=str, default="console", choices=["console", "file"], help="Log mode for the LLM kernel")
    parser.add_argument("--llm_backend", type=str, choices=["ollama", "vllm"], help="Backend to use for running the LLM kernel")
    
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

