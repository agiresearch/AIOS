from src.agents.agent_process import AgentProcess

import os

class BaseContextManager:
    def __init__(self):
        self.context_dir = os.path.join(os.getcwd(), "src", "context", "context_restoration")

    def start(self):
        pass

    def gen_snapshot(self, agent_process: AgentProcess):
        pass

    def gen_recover(self, agent_process: AgentProcess):
        pass

    def stop(self):
        pass
