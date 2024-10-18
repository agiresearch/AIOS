import time
from typing import List
from aios.hooks.request import send_request
from pyopenagi.agents.experiment.standard.action.action_tool import ActionTool
from pyopenagi.agents.experiment.standard.memory.short_term_memory import ShortTermMemory
from pyopenagi.agents.experiment.standard.planning.planning import Planning, DefaultPlanning
from pyopenagi.agents.experiment.standard.prompt.framework_prompt import STANDARD_PROMPT
from pyopenagi.agents.experiment.standard.utils.config import load_config
from pyopenagi.utils.chat_template import Query, Response
from pyopenagi.utils.logger import AgentLogger


class StandardAgent:

    def __init__(self, agent_name: str, task_input: str, log_mode: str):
        # Init module
        self.planning: Planning | None = None
        self.actions = {}
        self.communication = None
        self.memory = None
        self.short_term_memory = ShortTermMemory()

        # Init config and tool
        self.config = load_config()

        # Init agent base info
        self.agent_name = agent_name
        self.task_input = task_input
        self._init_framework_prompt()

        # Init logger
        self.logger = AgentLogger(agent_name, log_mode)

        # Init AIOS monitor info
        self.rounds = 0
        self.status = "active"
        self.start_time = None
        self.end_time = None
        self.request_waiting_times: list = []
        self.request_turnaround_times: list = []
        self.created_time = time.time()

    @property
    def messages(self):
        return self.short_term_memory.messages

    @property
    def tools_format(self):
        if "TOOL" in self.actions:
            return self.actions["TOOL"].tools_format
        else:
            return None

    def custom_prompt(self) -> str:
        pass

    def _init_framework_prompt(self):
        # Action
        action_prompt = self._action_prompt()
        planning_prompt = self._planning_prompt()

        framework_prompt = STANDARD_PROMPT.format(
            action=action_prompt,
            planning=planning_prompt,
        )

        self.short_term_memory.remember(role="system", content=framework_prompt)

    def _action_prompt(self) -> str:
        action_prompt = ""
        for action in self.actions:
            if action.disply:
                name = action.format_prompt()["name"]
                description = action.format_prompt()["description"]
                action_prompt += f"- {name}: {description}\n"

        return action_prompt

    def _planning_prompt(self) -> str:
        planning_prompt = ""

        name = self.planning.format_prompt()["name"]
        description = self.planning.format_prompt()["description"]
        planning_prompt += f"- {name}: {description}\n"
        return planning_prompt

    def init_module(self):
        return

    def init_planning(self, planning):
        self.planning = planning

    def init_communication(self, communication):
        return

    def init_memory(self, memory):
        return

    def init_actions(self, actions):
        action_tool = ActionTool()
        self.actions[action_tool.type] = action_tool

    def planning(self) -> dict:
        # Select suitable messages
        messages = self.short_term_memory.recall()

        planning = DefaultPlanning(self.request)
        result = planning(messages, self.tools_format)

        return result

    def run(self):
        # Init system prompt and task
        if custom_prompt := self.custom_prompt():
            self.short_term_memory.remember("system", custom_prompt)
        self.short_term_memory.remember("user", self.task_input)

        while not self._is_terminate():
            # Run planning
            planning_result = self.planning()
            if action_type := planning_result.action_type:
                action = self.actions[action_type]
                action_param = planning_result.action_param
                response, tool_call_id = action(**action_param)
                self.short_term_memory.remember("assistant", response, tool_call_id)
            else:
                response = planning_result.text_content
                self.short_term_memory.remember("assistant", response)

    def _is_terminate(self):
        return True if "TERMINATE" in self.short_term_memory.last_message else False

    def request(self, messages: List, tools: List) -> Response:
        (
            response,
            start_times,
            end_times,
            waiting_times,
            turnaround_times
        ) = send_request(
            agent_name=self.agent_name,
            query=Query(
                messages=messages,
                tools=tools,
                action_type="message_llm",
            )
        )

        # Update AIOS monitor info
        if self.rounds == 0:
            self.start_time = start_times[0]

        self.request_waiting_times.extend(waiting_times)
        self.request_turnaround_times.extend(turnaround_times)
        self.rounds += 1

        return response
