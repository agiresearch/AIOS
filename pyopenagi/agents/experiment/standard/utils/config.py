import json
import os
from typing import List

from pydantic.v1 import BaseModel


class Config(BaseModel):
    name: str
    description: List
    tools: List
    meta: dict
    build: dict


def load_config():
    script_path = os.path.abspath(__file__)
    script_dir = os.path.dirname(
        os.path.dirname(script_path)
    )
    config_file = os.path.join(script_dir, "config.json")
    with open(config_file, "r") as f:
        data = json.load(f)

    return Config(**data)
