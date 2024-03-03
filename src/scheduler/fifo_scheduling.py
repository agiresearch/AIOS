from base import BaseScheduler

import queue

import time

class FIFOScheduler(BaseScheduler):
    def __init__(self, agent_process_queue, llm):
        self.agent_process_queue = agent_process_queue
        self.llm = llm

    def schedule(self):
        while not process_queue.empty():
            current_process = agent_process_queue.get()
            address_request(agent_process)

    def address_request(self, agent_process):
        content = agent_process.prompt
        self.llm.address_request(content)
        

if __name__ == "__main__":
    # Example usage:
    
    FIFOScheduler(processes)