# This implements a (mostly) FIFO task queue using threads and queue, in a
# similar fashion to the round robin scheduler. However, the timeout is 1 second
# instead of 0.05 seconds.

from .base import BaseScheduler
from aios.hooks.types.llm import QueueGetMessage

from queue import Queue, Empty

import traceback
import time

class FIFOScheduler(BaseScheduler):
    def __init__(self, llm, log_mode, get_queue_message: QueueGetMessage):
        super().__init__(llm, log_mode)
        self.agent_process_queue = Queue()
        self.get_queue_message = get_queue_message

    def run(self):
        while self.active:
            try:
                """
                wait 1 second between each iteration at the minimum
                if there is nothing received in a second, it will raise Empty
                """

                agent_process = self.get_queue_message()
                agent_process.set_status("executing")
                self.logger.log(f"{agent_process.agent_name} is executing. \n", "execute")
                agent_process.set_start_time(time.time())
                self.execute_request(agent_process)
            except Empty:
                pass
            except Exception:
                traceback.print_exc()

    def execute_request(self, agent_process):
        self.llm.address_request(
            agent_process=agent_process
        )
