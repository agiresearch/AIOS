import random
import os
from typing import Optional


def generator_tool_call_id():
    """generate tool call id
    """
    return str(random.randint(0, 1000))

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