from pyopenagi.agents.agent_process import AgentProcessFactory
from typing import Optional

from aios.sdk.autogen.agent_adapter import (
    adapter_autogen_agent_init,
    _adapter_print_received_message,
    _adapter_generate_oai_reply_from_client,
    adapter_generate_tool_calls_reply,
    adapter_execute_function,
    _adapter_a_execute_tool_call,
    adapter_update_tool_signature
)

from aios.sdk.autogen.client_adapter import (
    adapter_autogen_client_init,
    adapter_client_create,
    adapter_client_extract_text_or_completion_object
)

from aios.utils.logger import AgentLogger

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

logger = AgentLogger("Adapter")


def prepare_autogen(agent_process_factory: Optional[AgentProcessFactory] = None):
    """
    Replace OpenAIWrapper and ConversableAgent methods with aios's implementation.

    This function is used to adapt autogen's API to aios's API, and it is used
    internally by aios.

    Args:
        agent_process_factory: An optional AgentProcessFactory instance. \
            If agent_process_factory is set, all autogen agents will have the capability to call LLM models.
    """
    # Replace OpenAIWrapper method
    OpenAIWrapper.__init__ = adapter_autogen_client_init
    OpenAIWrapper.create = adapter_client_create
    OpenAIWrapper.extract_text_or_completion_object = adapter_client_extract_text_or_completion_object

    # Replace agent method  
    ConversableAgent.agent_process_factory = agent_process_factory
    ConversableAgent._print_received_message = _adapter_print_received_message
    ConversableAgent._generate_oai_reply_from_client = _adapter_generate_oai_reply_from_client
    ConversableAgent.generate_tool_calls_reply = adapter_generate_tool_calls_reply
    ConversableAgent.execute_function = adapter_execute_function
    ConversableAgent._a_execute_tool_call = _adapter_a_execute_tool_call
    ConversableAgent.update_tool_signature = adapter_update_tool_signature
    ConversableAgent.__init__ = adapter_autogen_agent_init

    logger.log("Autogen prepare success", "info")
