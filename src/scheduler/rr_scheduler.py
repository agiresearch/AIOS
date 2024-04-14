from src.scheduler.base import BaseScheduler

from src.scheduler.base import BaseScheduler

from queue import Queue, Empty
from threading import Thread

import time

from src.context.simple_context import SimpleContextManager

class RRScheduler(BaseScheduler):
    def __init__(self, llm, log_mode):
        super().__init__(llm, log_mode)
        self.agent_process_queue = Queue()
        self.time_limit = 20
        self.simple_context_manager = SimpleContextManager()

    def run(self):
        while self.active:
            try:
                agent_process = self.agent_process_queue.get(block=True, timeout=1)
                agent_process.set_time_limit(self.time_limit)

                agent_process.set_status("executing")
                self.logger.log(f"{agent_process.agent_name} is switched to executing.\n", level="execute")
                agent_process.set_start_time(time.time())
                self.execute_request(agent_process)
                if agent_process.get_status() != "done":
                    self.logger.log(
                        f"{agent_process.agent_name} is switched to suspending due to the reach of time limit ({self.time_limit}s). \n",
                        level="suspend"
                    )

            except Empty:
                pass

    def execute_request(self, agent_request):
        self.llm.address_request(agent_request)
