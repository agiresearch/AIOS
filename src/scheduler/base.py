from queue import Queue, Empty
from threading import Thread

from src.utils.utils import (
    logger
)

from src.agents.agent_process import AgentProcess

import time

class BaseScheduler:
    def __init__(self, llm):
        self.active = False # start/stop the scheduler
        self.thread = Thread(target=self.run)
        self.llm = llm

    def run(self):
        pass
    
    def start(self):
        """start the scheduler"""
        self.active = True
        self.thread.start()

    def stop(self):
        """stop the scheduler"""
        self.active = False
        self.thread.join()

    def execute_request(self, agent_process: AgentProcess):
        agent_process.set_status("Executing")
        logger.info(f"{agent_process.agent_name} is executing.")
        agent_process.set_start_time(time.time())
        response = self.llm.address_request(agent_process.prompt)
        agent_process.set_response(response)
        agent_process.set_end_time(time.time())
        agent_process.set_status("Done")
