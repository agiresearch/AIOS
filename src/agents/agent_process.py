import os

import time

from datetime import datetime

from queue import Queue

class AgentProcess:
    def __init__(self, agent_name, prompt, agent_id=None):
        self.agent_id = agent_id
        self.agent_name = agent_name
        self.prompt = prompt
        self.response = None

    def set_created_time(self, time):
        self.created_time = time

    def get_created_time(self):
        return self.created_time

    def set_start_time(self, time):
        self.start_time = time

    def get_start_time(self):
        return self.start_time

    def set_end_time(self, time):
        self.end_time = time

    def get_end_time(self):
        return self.end_time

    def set_priority(self, priority):
        self.priority = priority

    def get_priority(self):
        return self.priority

    def set_status(self, status):
        self.status = status

    def get_status(self):
        return self.status

    def set_pid(self, pid):
        self.pid = pid

    def get_pid(self):
        return self.get_pid()

    def get_response(self):
        return self.response

    def set_response(self, response):
        self.response = response
