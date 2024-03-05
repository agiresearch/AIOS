import os

import time

from datetime import datetime

from queue import Queue

class AgentProcess:
    def __init__(self, agent_id, agent_name, prompt):
        self.agent_id = agent_id
        self.agent_name = agent_name
        self.prompt = prompt
        self.response = None

    def set_time(self, time):
        self.time = time

    def set_priority(self, priority):
        self.priority = priority

    def get_priority(self):
        return self.priority

    def get_time(self):
        return self.time

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

class AgentProcessQueue:
    def __init__(self):
        self.MAX_PID = 1024

        self.pid_pool = [False for i in range(self.MAX_PID)]
        
        self.agent_process_queue = [] # Currently use list to simulate queue

    def add(self, agent_process):
        pid = -1
        for i, used in enumerate(self.pid_pool):
            if not used:
                idx = i
                break
        if idx != -1:
            agent_process.set_pid(pid)
            agent_process.set_time(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            self.agent_process_queue.append(agent_process)
            agent_process.set_status("Waiting")

    def print(self):
        # print(self.agent_process_queue.size())
        # print(len(self.agent_process_queue))
        for agent_process in self.agent_process_queue:
            print(f"| Agent-process ID: {agent_process.get_pid()} | Status: {agent_process.get_status()} |")
