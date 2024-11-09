import functools
from typing import Annotated

from autogen import ConversableAgent

from aios.sdk import prepare_framework, FrameworkType
from experiment.agent.experiment_agent import ExpirementAgent
from pyopenagi.tools.arxiv.arxiv import Arxiv


class AutoGenAgent(ExpirementAgent):
    _TERMINATION = "<TERMINATION>"

    def __init__(self, on_aios: bool = True):
        if on_aios:
            prepare_framework(FrameworkType.AutoGen)

    def run(self, input_str: str):
        assistant_sender = ConversableAgent(
            name="assistant_1",
            system_message="Your name is assistant_1. When you think task is finished, say <TERMINATION>.",
            human_input_mode="NEVER"
        )

        assistant_recipient = ConversableAgent(
            name="assistant_2",
            is_termination_msg=lambda msg: msg.get("content") is not None and self._TERMINATION in msg["content"],
            human_input_mode="NEVER"
        )

        chat_result = assistant_sender.initiate_chat(assistant_recipient, message=input_str, max_turns=20)

        chat_history = chat_result.chat_history
        for message in reversed(chat_history):
            if "```patch" in message["content"]:
                result = message["content"]
                print(f"AutoGen result is: {result}")
                return message["content"]

        return ""


class AutoGenAgentGAIA(ExpirementAgent):

    SYSTEM_PROMPT = """You are a general AI assistant. I will ask you a question. Report your thoughts, and finish
    your answer with the following template: FINAL ANSWER: [YOUR FINAL ANSWER].
    YOUR FINAL ANSWER should be a number OR as few words as possible OR a comma separated list of
    numbers and/or strings.
    If you are asked for a number, don’t use comma to write your number neither use units such as $ or percent
    sign unless specified otherwise.
    If you are asked for a string, don’t use articles, neither abbreviations (e.g. for cities), and write the digits in
    plain text unless specified otherwise.
    If you are asked for a comma separated list, apply the above rules depending of whether the element to be put
    in the list is a number or a string."""

    _TERMINATION = "FINAL ANSWER"

    def __init__(self, on_aios: bool = True):
        if on_aios:
            prepare_framework(FrameworkType.AutoGen)

    def run(self, input_str: str):
        assistant_sender = ConversableAgent(
            name="User",
            is_termination_msg=lambda msg: msg.get("content") is not None and self._TERMINATION in msg["content"],
            human_input_mode="NEVER"
        )

        assistant_recipient = ConversableAgent(
            name="Assistant",
            system_message=self.SYSTEM_PROMPT,
            human_input_mode="NEVER"
        )

        # register tools
        for tool in TOOL_COLLECTION:
            assistant_recipient.register_for_llm(
                name=tool["name"], description=tool["description"]
            )(tool["function"])

            assistant_sender.register_for_execution(name=tool["name"])(tool["function"])

        # start chat
        chat_result = assistant_sender.initiate_chat(assistant_recipient, message=input_str, max_turns=20)

        chat_history = chat_result.chat_history
        for message in reversed(chat_history):
            if "FINAL ANSWER" in message["content"]:
                result = message["content"]
                print(f"AutoGen result is: {result}")
                return message["content"]

        return ""


class AutoGenAgentHumanEval(ExpirementAgent):

    SYSTEM_PROMPT = """You are an AI assistant good at coding. You will receive a function definition and
    comments. You need to help me complete this function. I will help you check your code. If you think it is ok to
    give the final answer. Give me final output in the format:
    <FINAL ANSWER>
        YOUR FINAL ANSWER (YOUR FINAL ANSWER must be a piece of code that you want to add. Just
        contains what you add, don't contains original definition and comments)
    </FINAL ANSWER>
    Don’t rush to provide the final result; you can first try asking me if the code is correct."""

    USER_PROMPT = """You are a software engineer. You will check the code written by Assistant and help Assistant
    optimize code."""

    _TERMINATION = "</FINAL ANSWER>"

    def __init__(self, on_aios: bool = True):
        if on_aios:
            prepare_framework(FrameworkType.AutoGen)

    def run(self, input_str: str):
        assistant_sender = ConversableAgent(
            name="User",
            is_termination_msg=lambda msg: msg.get("content") is not None and self._TERMINATION in msg["content"],
            human_input_mode="NEVER"
        )

        assistant_recipient = ConversableAgent(
            name="Assistant",
            system_message=self.SYSTEM_PROMPT,
            human_input_mode="NEVER"
        )

        # start chat
        chat_result = assistant_sender.initiate_chat(assistant_recipient, message=input_str, max_turns=20)

        chat_history = chat_result.chat_history
        for message in reversed(chat_history):
            if self._TERMINATION in message["content"]:
                result = message["content"]

                print(f"AutoGen result is: {result}")
                return result

        return ""


TOOL_COLLECTION = []


def add_tool(description: str):
    def add_tool_helper(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)

        func_name = func.__name__
        TOOL_COLLECTION.append({
            "name": func_name,
            "description": description,
            "function": func
        })
        return wrapper

    return add_tool_helper


@add_tool(description="Query articles or topics in arxiv")
def arxiv(
        query: Annotated[str, "Input query that describes what to search in arxiv"]
) -> str:
    arxiv_obj = Arxiv()

    tool_param = {
        "query": query,
    }
    return arxiv_obj.run(tool_param)


@add_tool(description="Search information using google search api")
def google_search(
        query: Annotated[str, "Prompt description of the image to be generated"]
) -> str:
    arxiv_obj = Arxiv()

    tool_param = {
        "query": query,
    }
    return arxiv_obj.run(tool_param)
