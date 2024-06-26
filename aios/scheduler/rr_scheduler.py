# Implementing a round robin scheduler using threads
# Allows multiple agents to run at the same time, with each getting a fixed
# chunk of processor time

from .base import BaseScheduler


# allows for memory to be shared safely between threads
from queue import Queue, Empty


from ..context.simple_context import SimpleContextManager

class RRScheduler(BaseScheduler):
    def __init__(self, llm, log_mode):
        super().__init__(llm, log_mode)
        self.agent_process_queue = Queue()
        self.time_limit = 5
        self.simple_context_manager = SimpleContextManager()

    def run(self):
        while self.active:
            try:
                """
                wait 0.05 seconds between each iteration at the minimum
                if there is nothing received in a second, it will raise Empty
                """
                agent_process = self.agent_process_queue.get(block=True, timeout=0.05)
                agent_process.set_time_limit(self.time_limit)

                agent_process.set_status("executing")
                # self.logger.log(f"{agent_process.agent_name} is switched to executing.\n", level="execute")
                self.execute_request(agent_process)

            except Empty:
                pass

    def execute_request(self, agent_request):
        """ called in multiple threads """
        self.llm.address_request(agent_request)
