# Support third-party frameworks running on AIOS.
import functools
from enum import Enum
from aios.utils.logger import SDKLogger

logger = SDKLogger("Adapter")


class FrameworkType(Enum):
    MetaGPT = "MetaGPT"
    OpenInterpreter = "Open-Interpreter"
    AutoGen = "AutoGen~0.2"


FRAMEWORK_ADAPTER = {}


def add_framework_adapter(framework_type: str):
    def add_framework_adapter_helper(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)

        FRAMEWORK_ADAPTER[framework_type] = func
        return wrapper

    return add_framework_adapter_helper


def prepare_framework(framework_type: FrameworkType):
    """
    Prepare the framework adapter for AIOS.

    This function is called by the framework before the user code is executed.
    It will call the adapter function associated with the given framework type.
    If the framework is not supported, it will log a warning message.

    Args:
        framework_type (str): The type of framework to prepare.
    """
    print(FRAMEWORK_ADAPTER)
    if framework_type.value not in FRAMEWORK_ADAPTER:
        logger.log(f"Framework {framework_type.value} are not supported.", "error")
    else:
        adapter = FRAMEWORK_ADAPTER[framework_type.value]
        adapter()
