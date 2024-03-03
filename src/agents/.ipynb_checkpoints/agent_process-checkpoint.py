import os

import time

from queue import Queue

class AgentProcess:
    def __init__(self, agent_id, agent_name, prompt):
        self.agent_id = agent_id
        self.agent_name = agent_name
        self.prompt = prompt

    def set_time(self):
        self.time = time.time()

    def set_priority(self, priority):
        self.priority = priority

    def get_priority(self):
        return self.priority

    def get_time(self):
        return self.time


class AgentProcessQueue:
    def __init__(self):
        self.queue = Queue()

    def add(self, agent_process):
        agent_process.set_time()
        self.queue.put(agent_process)