from src.scheduler.base import BaseScheduler

import queue

import time

from src.utils.global_param import (
    thread_pool,
    agent_process_queue
)

class FIFOScheduler(BaseScheduler):
    def __init__(self, llm):
        # self.agent_process_queue = agent_process_queue
        self.llm = llm
        # self.thread_pool = thread_pool

    def run(self):
        runner = thread_pool.submit(self.schedule)
        
    def schedule(self):
        while True:
            if not agent_process_queue.empty():
                current_process = agent_process_queue.pop(0)
                current_process.set_status("Running")
                result = self.address_request(agent_process)
                agent_process.set_response(response)

    def address_request(self, agent_process):
        content = agent_process.prompt
        result = self.llm.address_request(content)
        return result
        

if __name__ == "__main__":
    # Example usage:
    FIFOScheduler(processes)