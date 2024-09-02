# Modify BaseLLM method in metagpt
# Adapte metagpt to run LLM in aios
from typing import Union, Optional
from aios.utils.logger import SDKLogger
from pyopenagi.agents.agent_process import AgentProcessFactory
from pyopenagi.agents.call_core import CallCore
from pyopenagi.utils.chat_template import Query
from .config_adapter import prepare_metagpt_config

try:
    from metagpt.provider.base_llm import BaseLLM
    from metagpt.const import USE_CONFIG_TIMEOUT
    from metagpt.logs import logger as metagpt_logger

except ImportError:
    raise ImportError(
        "Could not import metagpt python package. "
        "Please install it with `pip install --upgrade metagpt`."
    )

logger = SDKLogger("MetaGPT Adapter")

aios_call = None


def prepare_metagpt(agent_process_factory: AgentProcessFactory):
    # create fake configuration file
    prepare_metagpt_config()

    # replace llm in metagpt with aios_call
    global aios_call
    if aios_call is None:
        aios_call = CallCore("metagpt", agent_process_factory, "console")
    BaseLLM.aask = adapter_aask


async def adapter_aask(
        self,
        msg: Union[str, list[dict[str, str]]],
        system_msgs: Optional[list[str]] = None,
        format_msgs: Optional[list[dict[str, str]]] = None,
        images: Optional[Union[str, list[str]]] = None,
        timeout=USE_CONFIG_TIMEOUT,
        stream=True,
) -> str:
    if system_msgs:
        message = self._system_msgs(system_msgs)
    else:
        message = [self._default_system_msg()]
    if not self.use_system_prompt:
        message = []
    if format_msgs:
        message.extend(format_msgs)
    if isinstance(msg, str):
        message.append(self._user_msg(msg, images=images))
    else:
        message.extend(msg)
    metagpt_logger.debug(message)
    rsp = await adapter_acompletion_text(message, stream=stream, timeout=self.get_timeout(timeout))
    return rsp if rsp else ""


async def adapter_acompletion_text(
        messages: list[dict], stream: bool = False, timeout: int = USE_CONFIG_TIMEOUT
) -> str:
    """Asynchronous version of completion. Return str. Support stream-print"""
    if stream:
        logger.log('''AIOS does not support stream mode currently. The stream mode has been automatically set to False.
                           ''', level="warn")
        stream = False

    # call aios for response
    global aios_call
    assert isinstance(aios_call, CallCore)
    response, _, _, _, _ = aios_call.get_response(
        query=Query(
            messages=messages,
            tools=None
        )
    )

    # return text
    text = response.response_message
    logger.log(f"\n{text}", "info")
    return response.response_message
