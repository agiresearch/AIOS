from src.agents.agent_process import AgentProcess

from src.context.base import BaseContextManager

import os

import torch

class SimpleContextManager(BaseContextManager):
    def __init__(self):
        pass

    def start(self):
        pass

    def gen_snapshot(self, pid, context):
        file_path = os.path.join(self.context_dir, f"{pid}.pt")
        torch.save(context, file_path)

    def gen_recover(self, pid):
        file_path = os.path.join(self.context_dir, f"{pid}.pt")
        return torch.load(file_path)

    def check_restoration(self, pid):
        return os.path.exists(os.path.join(self.context_dir, f"{pid}.pt"))

    def stop(self):
        pass
