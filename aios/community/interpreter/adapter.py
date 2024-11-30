# replace run_tool_calling_llm and run_text_llm in interpreter llm
# so that interpreter can run LLM in aios
import json
import sys

from aios.hooks.syscall import useSysCall
from aios.community.adapter import add_framework_adapter
from aios.utils.logger import SDKLogger
from cerebrum.llm.communication import LLMQuery
from dataclasses import dataclass

try:
    from interpreter import interpreter

except ImportError:
    raise ImportError(
        "Could not import interpreter python package. "
        "Please install it with `pip install open-interpreter`."
    )

logger = SDKLogger("Interpreter Adapter")
send_request, _ = useSysCall()

@add_framework_adapter("Open-Interpreter")
def prepare_interpreter():
    """Prepare the interpreter for running LLM in aios.
    """

    try:
        # Set the completion function in the interpreter
        interpreter.llm.completions = adapter_aios_completions

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
        logger.log("AIOS does not support stream mode currently."
                   "The stream mode has been automatically set to False.", level="warn")
        params["stream"] = False

    # Run completion
    attempts = 2
    first_error = None

    for attempt in range(attempts):
        try:
            response, _, _, _, _ = send_request(
                agent_name="Open-Interpreter",
                query=LLMQuery(
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
