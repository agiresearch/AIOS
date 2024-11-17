# Implementing a round robin scheduler using threads
# Allows multiple agents to run at the same time, with each getting a fixed
# chunk of processor time

from .base import BaseScheduler


# allows for memory to be shared safely between threads
from queue import Queue, Empty


from ..context.simple_context import SimpleContextManager

from aios.hooks.types.llm import LLMRequestQueueGetMessage
from aios.hooks.types.memory import MemoryRequestQueueGetMessage
from aios.hooks.types.tool import ToolRequestQueueGetMessage
from aios.hooks.types.storage import StorageRequestQueueGetMessage

from queue import Queue, Empty

import traceback
import time
from aios.utils.logger import SchedulerLogger

from threading import Thread

from .base import Scheduler


class RRScheduler(Scheduler):
    def __init__(
        self,
        llm,
        memory_manager,
        storage_manager,
        tool_manager,
        log_mode,
        get_llm_syscall: LLMRequestQueueGetMessage,
        get_memory_syscall: MemoryRequestQueueGetMessage,
        get_storage_syscall: StorageRequestQueueGetMessage,
        get_tool_syscall: ToolRequestQueueGetMessage,
    ):
        super().__init__(
            llm,
            memory_manager,
            storage_manager,
            tool_manager,
            log_mode,
            get_llm_syscall,
            get_memory_syscall,
            get_storage_syscall,
            get_tool_syscall,
        )
        self.llm = llm
        self.time_limit = 0.5
        self.simple_context_manager = SimpleContextManager()

    def run_llm_request(self):
        while self.active:
            try:
                llm_syscall = self.get_llm_request()

                llm_syscall.set_status("executing")
                self.logger.log(
                    f"{llm_syscall.agent_name} is executing. \n", "execute"
                )
                llm_syscall.set_start_time(time.time())

                response = self.llm.address_request(llm_syscall)
                llm_syscall.set_response(response)

                # self.llm.address_request(agent_request)

                llm_syscall.event.set()
                llm_syscall.set_status("done")
                llm_syscall.set_end_time(time.time())

                self.logger.log(
                    f"Current request of {llm_syscall.agent_name} is done. Thread ID is {llm_syscall.get_pid()}\n",
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

    def run_storage_request(self):
        while self.active:
            try:
                # wait at a fixed time interval, if there is nothing received in the time interval, it will raise Empty
                agent_request = self.get_memory_request()

                agent_request.set_status("executing")
                self.logger.log(
                    f"{agent_request.agent_name} is executing. \n", "execute"
                )
                agent_request.set_start_time(time.time())

                response = self.storage_manager.address_request(agent_request)
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

    def run_tool_request(self):
        while self.active:
            try:
                # wait at a fixed time interval, if there is nothing received in the time interval, it will raise Empty
                agent_request = self.get_memory_request()

                agent_request.set_status("executing")
                self.logger.log(
                    f"{agent_request.agent_name} is executing. \n", "execute"
                )
                agent_request.set_start_time(time.time())

                response = self.tool_manager.address_request(agent_request)
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
