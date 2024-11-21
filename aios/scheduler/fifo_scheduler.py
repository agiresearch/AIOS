# This implements a (mostly) FIFO task queue using threads and queue, in a
# similar fashion to the round robin scheduler. However, the timeout is 1 second
# instead of 0.05 seconds.

from aios.hooks.types.llm import LLMRequestQueueGetMessage
from aios.hooks.types.memory import MemoryRequestQueueGetMessage
from aios.hooks.types.tool import ToolRequestQueueGetMessage
from aios.hooks.types.storage import StorageRequestQueueGetMessage

from aios.memory.manager import MemoryManager
from aios.storage.storage import StorageManager
from aios.llm_core.adapter import LLMAdapter
from aios.tool.manager import ToolManager

from .base import Scheduler

from queue import Empty

import traceback
import time

class FIFOScheduler(Scheduler):
    def __init__(
        self,
        llm: LLMAdapter,
        memory_manager: MemoryManager,
        storage_manager: StorageManager,
        tool_manager: ToolManager,
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

    def run_llm_syscall(self):
        while self.active:
            try:
                # wait at a fixed time interval, if there is nothing received in the time interval, it will raise Empty
                llm_syscall = self.get_llm_syscall()

                llm_syscall.set_status("executing")
                self.logger.log(
                    f"{llm_syscall.agent_name} is executing. \n", "execute"
                )
                llm_syscall.set_start_time(time.time())

                response = self.llm.address_syscall(llm_syscall)
                llm_syscall.set_response(response)

                llm_syscall.event.set()
                llm_syscall.set_status("done")
                llm_syscall.set_end_time(time.time())

            except Empty:
                pass

            except Exception:
                traceback.print_exc()

    def run_memory_syscall(self):
        while self.active:
            try:
                # wait at a fixed time interval, if there is nothing received in the time interval, it will raise Empty
                memory_syscall = self.get_memory_syscall()

                memory_syscall.set_status("executing")
                self.logger.log(
                    f"{memory_syscall.agent_name} is executing. \n", "execute"
                )
                memory_syscall.set_start_time(time.time())

                response = self.memory_manager.address_request(memory_syscall)
                memory_syscall.set_response(response)

                memory_syscall.event.set()
                memory_syscall.set_status("done")
                memory_syscall.set_end_time(time.time())

            except Empty:
                pass

            except Exception:
                traceback.print_exc()

    def run_storage_syscall(self):
        while self.active:
            try:
                storage_syscall = self.get_storage_syscall()

                storage_syscall.set_status("executing")
                self.logger.log(
                    f"{storage_syscall.agent_name} is executing. \n", "execute"
                )
                storage_syscall.set_start_time(time.time())

                response = self.storage_manager.address_request(storage_syscall)
                storage_syscall.set_response(response)

                storage_syscall.event.set()
                storage_syscall.set_status("done")
                storage_syscall.set_end_time(time.time())

                self.logger.log(
                    f"Current request of {storage_syscall.agent_name} is done. Thread ID is {storage_syscall.get_pid()}\n",
                    "done"
                )

            except Empty:
                pass

            except Exception:
                traceback.print_exc()

    def run_tool_syscall(self):
        while self.active:
            try:
                tool_syscall = self.get_tool_syscall()

                tool_syscall.set_status("executing")

                tool_syscall.set_start_time(time.time())

                response = self.tool_manager.address_request(tool_syscall)
                tool_syscall.set_response(response)

                tool_syscall.event.set()
                tool_syscall.set_status("done")
                tool_syscall.set_end_time(time.time())

            except Empty:
                pass

            except Exception:
                traceback.print_exc()
