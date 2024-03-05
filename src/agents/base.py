import os

import json

from src.agents.agent_process import (
    AgentProcess,
    AgentProcessQueue
)

from src.utils.global_param import (
    thread_pool,
    agent_process_queue,
    MAX_AID,
    aid_pool,
    agent_pool
)

from datetime import datetime

class BaseAgent:
    def __init__(self, agent_name, task_input):
        self.agent_name = agent_name
        self.config = self.load_config()
        self.prefix = self.config["description"]
        self.task_input = task_input

        aid = -1
        for id, used in enumerate(aid_pool):
            if used is False:
                aid = id
                aid_pool[id] = True
                break
                
        self.set_aid(aid)
        time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
        # self.memory_pool = SingleMemory()
        
        self.set_status("Active")
        self.set_created_time(time)
        
        
    def run(self):
        '''Execute each step to finish the task.'''
        pass

    def load_config(self):
        config_file = os.path.join(os.getcwd(), "src", "agents", "agent_config/{}.json".format(self.agent_name))
        with open(config_file, "r") as f:
            config = json.load(f)
            return config

    def send_request(self, process):
        agent_process_queue.add(process)

    def get_response(self, process):
        while process.get_response() is None:
            pass

    def set_aid(self, aid):
        self.aid = aid

    def get_aid(self):
        return self.aid

    def get_agent_name(self):
        return self.agent_name

    def set_status(self, status):

        """
        Status type: Waiting, Running, Done, Inactive
        """
        self.status = status

    def get_status(self):
        return self.status

    def set_created_time(self, time):
        self.created_time = time

    def get_created_time(self):
        return self.created_time

    def parse_result(self, prompt):
        pass
        