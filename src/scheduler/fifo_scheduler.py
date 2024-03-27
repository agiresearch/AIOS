from src.scheduler.base import BaseScheduler

import queue

import time

from queue import Queue, Empty
from threading import Thread

class FIFOScheduler(BaseScheduler):
    def __init__(self, llm):
        self.agent_process_queue = Queue()
        # start/stop the scheduler
        self.active = False
        # thread
        self.thread = Thread(target=self.run)
        self.llm = llm

    def run(self):
        while self.active:
            try:
                agent_request = self.agent_process_queue.get(block=True, timeout=1)
                self.execute_request(agent_request)
            except Empty:
                pass