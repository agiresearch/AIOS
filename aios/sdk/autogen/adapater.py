from aios.sdk.autogen.agent_adapter import (
    adapter_autogen_agent_init,
    _adapter_print_received_message,
    _adapter_generate_oai_reply_from_client,
    adapter_generate_tool_calls_reply,
    adapter_execute_function,
    adapter_update_tool_signature
)
from aios.utils.logger import BaseLogger

try:
    from autogen import (
        OpenAIWrapper,
        ConversableAgent
    )
except ImportError:
    raise ImportError(
        "Could not import autogen python package. "
        "Please install it with `pip install pyautogen`."
    )

logger = BaseLogger("Adapter")


def prepare_autogen():
    """adapter autogen for aios
    """
    # Replace agent method
    ConversableAgent.__init__ = adapter_autogen_agent_init
    ConversableAgent._print_received_message = _adapter_print_received_message
    ConversableAgent._generate_oai_reply_from_client = _adapter_generate_oai_reply_from_client
    ConversableAgent.generate_tool_calls_reply = adapter_generate_tool_calls_reply
    ConversableAgent.execute_function = adapter_execute_function
    ConversableAgent.update_tool_signature = adapter_update_tool_signature

    logger.log("Autogen prepare success", "info")
