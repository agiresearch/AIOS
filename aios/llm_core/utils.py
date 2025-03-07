import json
import re
import uuid

def tool_calling_input_format(messages: list, tools: list) -> list:
    """Integrate tool information into the messages for open-sourced LLMs

    Args:
        messages (list): messages with different roles
        tools (list): tool information
    """
    prefix_prompt = (
        "In and only in current step, you need to call tools. Available tools are: "
    )
    tool_prompt = json.dumps(tools)
    suffix_prompt = "".join(
        [
            "Must call functions that are available. To call a function, respond "
            "immediately and only with a list of JSON object of the following format:"
            '[{"name":"function_name_value","parameters":{"parameter_name1":"parameter_value1",'
            '"parameter_name2":"parameter_value2"}}]'
        ]
    )

    # translate tool call message for models don't support tool call
    for message in messages:
        if "tool_calls" in message:
            message["content"] = json.dumps(message.pop("tool_calls"))
            
        elif message["role"] == "tool":
            message["role"] = "user"
            tool_call_id = message.pop("tool_call_id")
            content = message.pop("content")
            message["content"] = (
                f"The result of the execution of function(id :{tool_call_id}) is: {content}. "
            )

    messages[-1]["content"] += prefix_prompt + tool_prompt + suffix_prompt
    return messages

def parse_json_format(message: str) -> str:
    json_array_pattern = r"\[\s*\{.*?\}\s*\]"
    json_object_pattern = r"\{\s*.*?\s*\}"

    match_array = re.search(json_array_pattern, message)

    if match_array:
        json_array_substring = match_array.group(0)

        try:
            json_array_data = json.loads(json_array_substring)
            return json.dumps(json_array_data)
        except json.JSONDecodeError:
            pass

    match_object = re.search(json_object_pattern, message)

    if match_object:
        json_object_substring = match_object.group(0)

        try:
            json_object_data = json.loads(json_object_substring)
            return json.dumps(json_object_data)
        except json.JSONDecodeError:
            pass
    return "[]"

def generator_tool_call_id():
    return str(uuid.uuid4())

def decode_litellm_tool_calls(response):
    tool_calls = response.choices[0].message.tool_calls
    
    decoded_tool_calls = []
    for tool_call in tool_calls:
        decoded_tool_calls.append(
            {
                "name": tool_call.function.name,
                "parameters": tool_call.function.arguments,
                "id": tool_call.id
            }
        )
        
    return decoded_tool_calls

def parse_tool_calls(message):
    # add tool call id and type for models don't support tool call
    # if isinstance(message, dict):
    #     message = [message]
    # tool_calls = json.loads(parse_json_format(message))
    tool_calls = json.loads(message)
    # breakpoint()
    # tool_calls = json.loads(message)
    if isinstance(tool_calls, dict):
        tool_calls = [tool_calls]
        
    for tool_call in tool_calls:
        tool_call["id"] = generator_tool_call_id()
        # if "function" in tool_call:
        
    tool_calls = double_underscore_to_slash(tool_calls)
        # tool_call["type"] = "function"
    return tool_calls

def slash_to_double_underscore(tools):
    for tool in tools:
        tool_name = tool["function"]["name"]
        if "/" in tool_name:
            tool_name = "__".join(tool_name.split("/"))
            tool["function"]["name"] = tool_name
    return tools

def double_underscore_to_slash(tool_calls):
    for tool_call in tool_calls:
        tool_call["name"] = tool_call["name"].replace("__", "/")
        tool_call["parameters"] = json.loads(tool_call["parameters"])
    return tool_calls

def pre_process_tools(tools):
    for tool in tools:
        tool_name = tool["function"]["name"]
        if "/" in tool_name:
            tool_name = "__".join(tool_name.split("/"))
            tool["function"]["name"] = tool_name
    return tools