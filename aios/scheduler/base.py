from abc import ABC, abstractmethod
from threading import Thread
from typing import List, Callable, Dict, Any
import logging

from aios.hooks.types.llm import LLMRequestQueueGetMessage
from aios.hooks.types.memory import MemoryRequestQueueGetMessage
from aios.hooks.types.tool import ToolRequestQueueGetMessage
from aios.hooks.types.storage import StorageRequestQueueGetMessage
from aios.utils.logger import SchedulerLogger
from aios.memory.manager import MemoryManager
from aios.storage.storage import StorageManager
from aios.llm_core.adapter import LLMAdapter
from aios.tool.manager import ToolManager

class BaseScheduler(ABC):
    """
    Abstract base class for all schedulers in the system.
    
    This class defines the common interface and functionality that all schedulers
    must implement, including request processing and thread management.
    
    Example:
        ```python
        class MyScheduler(BaseScheduler):
            def _process_llm_requests(self):
                # Implementation
                pass
                
            def _process_memory_requests(self):
                # Implementation
                pass
                
            # ... other required methods
        ```
    """
    
    def __init__(
        self,
        llm: LLMAdapter,
        memory_manager: MemoryManager,
        storage_manager: StorageManager,
        tool_manager: ToolManager,
        log_mode: str,
        get_llm_syscall: LLMRequestQueueGetMessage,
        get_memory_syscall: MemoryRequestQueueGetMessage,
        get_storage_syscall: StorageRequestQueueGetMessage,
        get_tool_syscall: ToolRequestQueueGetMessage,
    ):
        """
        Initialize the base scheduler.

        Args:
            llm: LLM adapter instance
            memory_manager: Memory management instance
            storage_manager: Storage management instance
            tool_manager: Tool management instance
            log_mode: Logging mode configuration
            get_llm_syscall: Function to get LLM syscalls
            get_memory_syscall: Function to get Memory syscalls
            get_storage_syscall: Function to get Storage syscalls
            get_tool_syscall: Function to get Tool syscalls
        """
        self.llm = llm
        self.memory_manager = memory_manager
        self.storage_manager = storage_manager
        self.tool_manager = tool_manager
        
        self.get_llm_syscall = get_llm_syscall
        self.get_memory_syscall = get_memory_syscall
        self.get_storage_syscall = get_storage_syscall
        self.get_tool_syscall = get_tool_syscall
        
        self.active = False
        self.log_mode = log_mode
        self.logger = self._setup_logger()
        
        self.processing_threads: Dict[str, Thread] = {}

    def _setup_logger(self) -> SchedulerLogger:
        """
        Set up the scheduler's logger.
        
        Returns:
            Configured SchedulerLogger instance
        """
        return SchedulerLogger(self.__class__.__name__, self.log_mode)

    def start_processing_threads(self, processors: List[Callable]) -> None:
        """
        Start processing threads for different request types.
        
        Args:
            processors: List of processor functions to run in threads
            
        Example:
            ```python
            scheduler.start_processing_threads([
                self.process_llm_requests,
                self.process_memory_requests
            ])
            ```
        """
        for processor in processors:
            thread_name = processor.__name__
            thread = Thread(target=processor, name=thread_name)
            self.processing_threads[thread_name] = thread
            thread.start()

    def stop_processing_threads(self) -> None:
        """
        Stop all processing threads gracefully.
        
        Example:
            ```python
            scheduler.stop_processing_threads()
            ```
        """
        for thread in self.processing_threads.values():
            thread.join()
        self.processing_threads.clear()

    @abstractmethod
    def process_llm_requests(self) -> None:
        """Process LLM requests from the queue."""
        pass
    
    @abstractmethod
    def process_memory_requests(self) -> None:
        """Process Memory requests from the queue."""
        pass
    
    @abstractmethod
    def process_storage_requests(self) -> None:
        """Process Storage requests from the queue."""
        pass

    @abstractmethod
    def process_tool_requests(self) -> None:
        """Process Tool requests from the queue."""
        pass
    
    @abstractmethod
    def start(self) -> None:
        """Start the scheduler."""
        pass

    @abstractmethod
    def stop(self) -> None:
        """Stop the scheduler."""
        pass
