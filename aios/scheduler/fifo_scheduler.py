# This implements a (mostly) FIFO task queue using threads and queue, in a
# similar fashion to the round robin scheduler. However, the timeout is 1 second
# instead of 0.05 seconds.

from aios.hooks.types.llm import LLMRequestQueueGetMessage
from aios.hooks.types.memory import MemoryRequestQueueGetMessage

from queue import Queue, Empty

import traceback
import time
from aios.utils.logger import SchedulerLogger

from threading import Thread


class FIFOScheduler:
    def __init__(
        self,
        llm,
        # memory_manager,
        log_mode,
        get_llm_request: LLMRequestQueueGetMessage,
        get_memory_request: MemoryRequestQueueGetMessage,
    ):
        self.agent_process_queue = Queue()
        self.get_llm_request = get_llm_request
        self.get_memory_request = get_memory_request
        self.active = False  # start/stop the scheduler
        self.log_mode = log_mode
        self.logger = self.setup_logger()
        # self.thread = Thread(target=self.run)
        self.request_processors = {
            "llm_request_processor": Thread(target=self.run_llm_request),
            # "memory_request_processor": Thread(self.run_memory_request)
        }
        self.llm = llm
        # self.memory_manager = memory_manager

    def start(self):
        """start the scheduler"""
        self.active = True
        for name, thread_value in self.request_processors.items():
            thread_value.start()

    def stop(self):
        """stop the scheduler"""
        self.active = False
        for name, thread_value in self.request_processors.items():
            thread_value.join()

    def setup_logger(self):
        logger = SchedulerLogger("Scheduler", self.log_mode)
        return logger

    def run_llm_request(self):
        while self.active:
            try:
                # wait at a fixed time interval, if there is nothing received in the time interval, it will raise Empty
                agent_request = self.get_llm_request()

                agent_request.set_status("executing")
                self.logger.log(
                    f"{agent_request.agent_name} is executing. \n", "execute"
                )
                agent_request.set_start_time(time.time())

                response = self.llm.address_request(agent_request)
                agent_request.set_response(response)

                # self.llm.address_request(agent_request)

                agent_request.event.set()
                agent_request.set_status("done")
                agent_request.set_end_time(time.time())

                self.logger.log(
                    f"Current request of {agent_request.agent_name} is done. Thread ID is {agent_request.get_pid()}\n",
                    "done",
                )
                # wait at a fixed time interval, if there is nothing received in the time interval, it will raise Empty

            except Empty:
                pass

            except Exception:
                traceback.print_exc()

    def run_memory_request(self):
        while self.active:
            try:
                # wait at a fixed time interval, if there is nothing received in the time interval, it will raise Empty
                agent_request = self.get_memory_request()

                agent_request.set_status("executing")
                self.logger.log(
                    f"{agent_request.agent_name} is executing. \n", "execute"
                )
                agent_request.set_start_time(time.time())

                response = self.memory_manager.address_request(agent_request)
                agent_request.set_response(response)

                # self.llm.address_request(agent_request)

                agent_request.event.set()
                agent_request.set_status("done")
                agent_request.set_end_time(time.time())

                self.logger.log(
                    f"Current request of {agent_request.agent_name} is done. Thread ID is {agent_request.get_pid()}\n",
                    "done",
                )
                # wait at a fixed time interval, if there is nothing received in the time interval, it will raise Empty

            except Empty:
                pass

            except Exception:
                traceback.print_exc()
