from src.scheduler.base import BaseScheduler

from src.scheduler.base import BaseScheduler

from queue import Queue, Empty
from threading import Thread

from src.agents.agent_process import AgentProcess
import time

from src.context.simple_context import SimpleContextManager

class RRScheduler(BaseScheduler):
    def __init__(self, llm, log_mode):
        super().__init__(llm, log_mode)
        self.agent_process_queue = Queue()
        self.time_limit = 5
        self.simple_context_manager = SimpleContextManager()

    def run(self):
        while self.active:
            try:
                agent_request = self.agent_process_queue.get(block=True, timeout=1)
                agent_request.set_time_limit(self.time_limit)
                self.execute_request(agent_request)
            except Empty:
                pass

    def execute_request(self, agent_request: AgentProcess):
        self.llm.address_request(agent_request)
