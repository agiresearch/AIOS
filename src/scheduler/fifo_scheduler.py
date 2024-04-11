from src.scheduler.base import BaseScheduler

from queue import Queue, Empty
from threading import Thread

import time
class FIFOScheduler(BaseScheduler):
    def __init__(self, llm, log_mode):
        super().__init__(llm, log_mode)
        self.agent_process_queue = Queue()


    def run(self):
        while self.active:
            try:
                agent_request = self.agent_process_queue.get(block=True, timeout=1)
                # print("Get the request")
                self.execute_request(agent_request)
            except Empty:
                pass

    def execute_request(self, agent_process):
        self.llm.address_request(
            agent_process=agent_process
        )
