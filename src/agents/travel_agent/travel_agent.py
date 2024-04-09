from src.agents.base import BaseAgent

import os

import time

import sys

from src.agents.agent_process import (
    AgentProcess
)

from concurrent.futures import as_completed

import numpy as np

from src.tools.online.bing_search import BingSearch

from src.tools.online.google_search import GoogleSearch

from src.tools.online.arxiv import Arxiv

class TravelAgent(BaseAgent):
    def __init__(self,
                 agent_name,
                 task_input,
                 llm,
                 agent_process_queue,
                 log_mode
        ):
        BaseAgent.__init__(self, agent_name, task_input, llm, agent_process_queue, log_mode)

        self.tool_list = {
            "google_search": GoogleSearch(),
            # "bing_search": BingSearch(),
            # "arxiv": Arxiv()
        }

        self.tool_calling_max_fail_times = 10

        self.tool_info = "".join(self.config["tool_info"])

        self.prefix = "".join(self.config["description"])

        # self.load_flow()

    def load_flow(self):
        # self.flow_ptr = Flow(self.config["flow"])
        return

    def run(self):
        # all_plans = []
        pass
