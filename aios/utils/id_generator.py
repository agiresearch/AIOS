import random


def generator_tool_call_id():
    """generate tool call id
    """
    return str(random.randint(0, 1000))
