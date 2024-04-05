from src.scheduler.base import BaseScheduler

from queue import Queue, Empty
from threading import Thread

class FIFOScheduler(BaseScheduler):
    def __init__(self, llm, log_mode):
        super().__init__(llm, log_mode)
        self.agent_process_queue = Queue()


    def run(self):
        while self.active:
            try:
                agent_request = self.agent_process_queue.get(block=True, timeout=1)
                self.execute_request(agent_request)
            except Empty:
                pass
