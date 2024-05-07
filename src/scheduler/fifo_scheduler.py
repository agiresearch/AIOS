from .base import BaseScheduler

from queue import Queue, Empty
from threading import Thread

import time
class FIFOScheduler(BaseScheduler):
    def __init__(self, llm, agent_process_queue, log_mode):
        super().__init__(llm, agent_process_queue, log_mode)

    def run(self):
        while self.active:
            try:
                agent_process = self.agent_process_queue.get(block=True, timeout=1)
                # print("Get the request")
                agent_process.set_status("executing")
                self.logger.log(f"{agent_process.agent_name} is executing. \n", "execute")
                agent_process.set_start_time(time.time())
                self.execute_request(agent_process)
            except Empty:
                pass

    def execute_request(self, agent_process):
        self.llm.address_request(
            agent_process=agent_process
        )
