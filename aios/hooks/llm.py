from aios.llm_core.llms import LLM

from aios.hooks.types.llm import LLMParams, SchedulerParams, LLMRequestQueue
from aios.hooks.validate import validate

from aios.hooks.stores import queue as QueueStore
import queue

from aios.hooks.utils import generate_random_string

@validate(LLMParams)
def useKernel(params: LLMParams) -> LLM:
    return LLM(**params.model_dump())

def useLLMRequestQueue() -> LLMRequestQueue:
    r_str = generate_random_string()
    QueueStore.LLM_REQUEST_QUEUE[r_str] = LLMRequestQueue()
    return QueueStore.LLM_REQUEST_QUEUE[r_str]

@validate(SchedulerParams)
def useScheduler(params: SchedulerParams):
    pass

@validate(SchedulerParams)
def useFIFOScheduler(params: SchedulerParams):
    pass

def useFactory():
    pass


# This implements a (mostly) FIFO task queue using threads and queue, in a
# similar fashion to the round robin scheduler. However, the timeout is 1 second
# instead of 0.05 seconds.

from .base import BaseScheduler

from queue import Queue, Empty

import time

from pyopenagi.queues.llm_request_queue import LLMRequestQueue

class FIFOScheduler(BaseScheduler):
    def __init__(self, llm, log_mode):
        super().__init__(llm, log_mode)
        self.agent_process_queue = Queue()


    def run(self):
        while self.active:
            try:
                """
                wait 1 second between each iteration at the minimum
                if there is nothing received in a second, it will raise Empty
                """
                # agent_process = self.agent_process_queue.get(block=True, timeout=1)
                agent_process = LLMRequestQueue.get_message()
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


# base implementation of the scheduler, sets up the threads and init
# which all sub classes will inherit and wouldn't need to change.

from threading import Thread

from aios.llm_core.llms import LLM

from aios.utils.logger import SchedulerLogger
class BaseScheduler:
    def __init__(self, llm: LLM, log_mode):
        self.active = False # start/stop the scheduler
        self.log_mode = log_mode
        self.logger = self.setup_logger()
        self.thread = Thread(target=self.run)
        self.llm = llm

    def run(self):
        pass

    def start(self):
        """start the scheduler"""
        self.active = True
        self.thread.start()

    def setup_logger(self):
        logger = SchedulerLogger("Scheduler", self.log_mode)
        return logger

    def stop(self):
        """stop the scheduler"""
        self.active = False
        self.thread.join()

    def execute_request(self, agent_process):
        pass
