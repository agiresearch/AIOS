# replace run_tool_calling_llm and run_text_llm in interpreter llm
# so that interpreter can run LLM in aios
import json
import sys

from aios.utils.logger import SDKLogger
from pyopenagi.agents.agent_process import AgentProcessFactory
from pyopenagi.utils.chat_template import Query
from pyopenagi.agents.call_core import CallCore
from dataclasses import dataclass

try:
    from interpreter import interpreter

except ImportError:
    raise ImportError(
        "Could not import interpreter python package. "
        "Please install it with `open-interpreter`."
    )

logger = SDKLogger("Interpreter Adapter")

aios_call = None


def prepare_interpreter(agent_process_factory: AgentProcessFactory):
    """Prepare the interpreter for running LLM in aios.

    Args:
        agent_process_factory (AgentProcessFactory):
            Used to create agent processes.
    """

    try:
        # Set the completion function in the interpreter
        interpreter.llm.completions = adapter_aios_completions

        # Initialize the aios_call variable as a CallCore object
        global aios_call
        aios_call = CallCore("interpreter", agent_process_factory, "console")
    except Exception as e:
        logger.log("Interpreter prepare failed: " + str(e) + "\n", "error")

    logger.log("Interpreter prepare success\n", "info")


@dataclass
class InterpreterFunctionAdapter:
    name: str
    arguments: str


@dataclass
class InterpreterToolCallsAdapter:
    function: InterpreterFunctionAdapter

    def __init__(self, name: str, arguments: str):
        self.function = InterpreterFunctionAdapter(name, arguments)


def adapter_aios_completions(**params):
    """aios completions replace fixed_litellm_completions in interpreter
    """

    if params.get("stream", False) is True:
        # TODO: AIOS not supprt stream mode
        logger.log('''AIOS does not support stream mode currently. The stream mode has been automatically set to False.
                   ''', level="warn")
        params["stream"] = False

    # Run completion
    attempts = 2
    first_error = None

    for attempt in range(attempts):
        try:
            global aios_call
            assert isinstance(aios_call, CallCore)
            response, _, _, _, _ = aios_call.get_response(
                query=Query(
                    messages=params['messages'],
                    tools=(params["tools"] if "tools" in params else None)
                )
            )

            # format similar to completion in interpreter
            comletion = {'choices':
                [
                    {
                        'delta': {}
                    }
                ]
            }
            comletion["choices"][0]["delta"]["content"] = response.response_message
            if response.tool_calls is not None:
                comletion["choices"][0]["delta"]["tool_calls"] = format_tool_calls_to_interpreter(response.tool_calls)

            return [comletion]  # If the completion is successful, exit the function
        except KeyboardInterrupt:
            print("Exiting...")
            sys.exit(0)
        except Exception as e:
            if attempt == 0:
                # Store the first error
                first_error = e

    if first_error is not None:
        raise first_error


def format_tool_calls_to_interpreter(tool_calls):
    name = tool_calls[0]["name"]
    arguments = tool_calls[0]["parameters"]
    arguments = json.dumps(arguments)
    return [InterpreterToolCallsAdapter(name, arguments)]
