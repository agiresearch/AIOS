import time
from typing import List

from aios.hooks.request import send_request
from pyopenagi.agents.experiment.standard.memory.short_term_memory import ShortTermMemory
from pyopenagi.agents.experiment.standard.planning.planning import Planning, DefaultPlanning
from pyopenagi.utils.chat_template import Query, Response
from pyopenagi.utils.logger import AgentLogger


class StandardAgent:

    def __init__(self, agent_name: str, task_input: str, log_mode: str):
        # Init module
        self.planning: Planning | None = None
        self.actions = None
        self.communication = None
        self.memory = None
        self.short_term_memory = ShortTermMemory()

        # Init agent base info
        self.agent_name = agent_name
        self.task_input = task_input

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

    def system_prompt(self) -> str:
        return """You are a smart agent."""

    def init_module(self):
        return

    def init_planning(self, planning):
        self.planning = planning

    def init_communication(self, communication):
        return

    def init_memory(self, memory):
        return

    def init_actions(self, actions):
        return

    def planning(self) -> dict:
        # Select suitable messages
        messages = self.short_term_memory.recall()

        planning = DefaultPlanning()
        result = planning(messages, self.tools)

        return result

    def run(self):
        # Init system prompt and task
        self.short_term_memory.remember("system", self.system_prompt())
        self.short_term_memory.remember("user", self.task_input)

        # Run planning
        # planning_result = self.planning()

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
