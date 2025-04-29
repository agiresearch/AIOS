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

from .base import BaseScheduler

import logging
from typing import Optional, Dict, Any, List

logger = logging.getLogger(__name__)

class RRScheduler(BaseScheduler):
    """
    Round Robin scheduler implementation that gives each task a fixed time slice.
    
    This scheduler ensures fair distribution of processing time among tasks by
    limiting each task's execution time and cycling through all tasks.
    
    Example:
        ```python
        scheduler = RRScheduler(
            ...
        )
        scheduler.start()
        ```
    """

    def __init__(self, *args, time_slice: float = 1, **kwargs):
        """
        Initialize the Round Robin Scheduler.
        
        Args:
            *args: Arguments passed to BaseScheduler
            time_slice: Time slice for each task in seconds
            **kwargs: Keyword arguments passed to BaseScheduler
        """
        super().__init__(*args, **kwargs)
        self.time_slice = time_slice
        self.context_manager = SimpleContextManager()
        
    def _execute_syscall(
        self, 
        syscall: Any,
        executor: Any,
        syscall_type: str
    ) -> Optional[Dict[str, Any]]:
        """
        Execute a system call with proper status tracking and error handling.
        
        Args:
            syscall: The system call to execute
            executor: Function to execute the syscall
            syscall_type: Type of the syscall for logging
            
        Returns:
            Optional[Dict[str, Any]]: Response from the syscall execution
            
        Example:
            ```python
            response = scheduler._execute_syscall(
                llm_syscall,
                self.llm.execute_llm_syscall,
                "LLM"
            )
            ```
        """
        try:
            syscall.set_status("executing")
            self.logger.log(
                f"{syscall.agent_name} is executing {syscall_type} syscall.\n",
                "executing"
            )
            syscall.set_start_time(time.time())

            response = executor(syscall)
            syscall.set_response(response)

            syscall.event.set()
            syscall.set_status("done")
            syscall.set_end_time(time.time())

            self.logger.log(
                f"Completed {syscall_type} syscall for {syscall.agent_name}. "
                f"Thread ID: {syscall.get_pid()}\n",
                "done"
            )
            
            return response

        except Exception as e:
            logger.error(f"Error executing {syscall_type} syscall: {str(e)}")
            traceback.print_exc()
            return None

        
    def _execute_batch_syscalls(
        self,
        batch: List[Any],
        executor: Any,
        syscall_type: str
    ) -> None:
        """
        Execute a batch of system calls with proper status tracking and error handling.

        Args:
            batch: The list of system calls to execute
            executor: Function to execute the batch of syscalls
            syscall_type: Type of the syscalls for logging
        """
        if not batch:
            return

        start_time = time.time()
        for syscall in batch:
            try:
                syscall.set_status("executing")
                syscall.set_time_limit(self.time_slice)
                
                logger.info(f"{syscall.agent_name} preparing batched {syscall_type} syscall.")
                syscall.set_start_time(start_time)
            except Exception as e:
                logger.error(f"Error preparing syscall {getattr(syscall, 'agent_name', 'unknown')} for batch execution: {str(e)}")
                continue

        if not batch:
            message = f"Empty batch after preparation for {syscall_type}, skipping execution."
            logger.warning(message)
            return

        logger.info(f"Executing batch of {len(batch)} {syscall_type} syscalls.")

        try:
            responses = executor(batch)

            for i, syscall in enumerate(batch):
                logger.info(f"Completed batched {syscall_type} syscall for {syscall.agent_name}. "
                    f"Thread ID: {syscall.get_pid()}\n")


        except Exception as e:
            logger.error(f"Error executing {syscall_type} syscall batch: {str(e)}")
            traceback.print_exc()

    def process_llm_requests(self) -> None:
        """
        Process LLM requests with time slicing.
        
        Example:
            ```python
            scheduler.process_llm_requests()
            # Processes LLM requests with 50ms time slices:
            # {
            #     "messages": [{"role": "user", "content": "Hello"}],
            #     "temperature": 0.7
            # }
            ```
        """
        while self.active:
            try:
                llm_syscall = self.get_llm_syscall()
                self._execute_batch_syscalls(llm_syscall, self.llm.execute_llm_syscalls, "LLM")
            except Empty:
                pass

    def process_memory_requests(self) -> None:
        """
        Process Memory requests with time slicing.
        
        Example:
            ```python
            scheduler.process_memory_requests()
            # Processes Memory requests with 50ms time slices:
            # {
            #     "operation": "store",
            #     "data": {"key": "value"}
            # }
            ```
        """
        while self.active:
            try:
                memory_syscall = self.get_memory_syscall()
                self._execute_syscall(
                    memory_syscall,
                    self.memory_manager.address_request,
                    "Memory"
                )
            except Empty:
                pass

    def process_storage_requests(self) -> None:
        """
        Process Storage requests with time slicing.
        
        Example:
            ```python
            scheduler.process_storage_requests()
            # Processes Storage requests with 50ms time slices:
            # {
            #     "operation": "write",
            #     "path": "/tmp/file.txt",
            #     "content": "Hello, World!"
            # }
            ```
        """
        while self.active:
            try:
                storage_syscall = self.get_storage_syscall()
                self._execute_syscall(
                    storage_syscall,
                    self.storage_manager.address_request,
                    "Storage"
                )
            except Empty:
                pass

    def process_tool_requests(self) -> None:
        """
        Process Tool requests with time slicing.
        
        Example:
            ```python
            scheduler.process_tool_requests()
            # Processes Tool requests with 50ms time slices:
            # {
            #     "name": "calculator",
            #     "arguments": {
            #         "operation": "add",
            #         "numbers": [1, 2]
            #     }
            # }
            ```
        """
        while self.active:
            try:
                tool_syscall = self.get_tool_syscall()
                self._execute_syscall(
                    tool_syscall,
                    self.tool_manager.address_request,
                    "Tool"
                )
            except Empty:
                pass

    def start(self) -> None:
        """
        Start all request processing threads.
        
        Example:
            ```python
            scheduler = RoundRobinScheduler(...)
            scheduler.start()
            # Starts processing all types of requests with time slicing
            ```
        """
        self.active = True
        self.start_processing_threads([
            self.process_llm_requests,
            self.process_memory_requests,
            self.process_storage_requests,
            self.process_tool_requests
        ])

    def stop(self) -> None:
        """
        Stop all request processing threads.
        
        Example:
            ```python
            scheduler.stop()
            # Stops all processing threads gracefully
            ```
        """
        self.active = False
        self.stop_processing_threads()
