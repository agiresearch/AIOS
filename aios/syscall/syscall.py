import time
import json
from typing import Dict, List, Any, Optional

# Update import to use the new location
from aios.memory.note import MemoryNote
from aios.syscall import Syscall
from aios.syscall.llm import LLMSyscall
from aios.syscall.storage import StorageSyscall, storage_syscalls
from aios.syscall.tool import ToolSyscall
from aios.syscall.memory import MemorySyscall
from aios.hooks.stores._global import (
    global_llm_req_queue_add_message,
    global_memory_req_queue_add_message,
    global_storage_req_queue_add_message,
    global_tool_req_queue_add_message,
    # global_llm_req_queue,
    # global_memory_req_queue,
    # global_storage_req_queue,
    # global_tool_req_queue,
)

import threading

from aios.hooks.types.llm import LLMRequestQueue
from aios.hooks.types.memory import MemoryRequestQueue
from aios.hooks.types.storage import StorageRequestQueue
from aios.hooks.types.tool import ToolRequestQueue

from cerebrum.llm.apis import LLMQuery, LLMResponse
from cerebrum.memory.apis import MemoryQuery, MemoryResponse
from cerebrum.storage.apis import StorageQuery, StorageResponse
from cerebrum.tool.apis import ToolQuery, ToolResponse

class SyscallExecutor:
    """
    A class that handles system call execution for different types of operations.
    
    This class provides methods to execute system calls for storage, memory,
    tools, and LLM operations, managing their lifecycle and responses.
    
    Example:
        ```python
        executor = SyscallExecutor()
        response = executor.execute_request("agent_1", LLMQuery(...))
        ```
    """
    
    def __init__(self):
        """Initialize the SyscallExecutor."""
        self.id = 0
        self.id_lock = threading.Lock()
    
    def create_syscall(self, agent_name: str, query) -> Dict[str, Any]:
        """
        Create a syscall object based on the query type.
        """
        if isinstance(query, LLMQuery):
            return LLMSyscall(agent_name, query)
        elif isinstance(query, StorageQuery):
            return StorageSyscall(agent_name, query)
        elif isinstance(query, MemoryQuery):
            return MemorySyscall(agent_name, query)
        elif isinstance(query, ToolQuery):
            return ToolSyscall(agent_name, query)

    def _execute_syscall(self, agent_name: str, query) -> Dict[str, Any]:
        """
        Execute a system call and collect timing metrics.
        
        Args:
            syscall: The system call object to execute
            
        Returns:
            Dict containing response and timing metrics
            
        Example:
            ```python
            syscall = StorageSyscall("agent_1", query)
            result = executor._execute_syscall(syscall)
            # Returns:
            {
                "response": "Operation completed",
                "start_times": [1234567890.123],
                "end_times": [1234567890.234],
                "waiting_times": [0.111],
                "turnaround_times": [0.222]
            }
            ```
        """
        completed_response = ""
        start_times, end_times = [], []
        waiting_times, turnaround_times = [], []

        with self.id_lock:
            self.id += 1
            syscall_id = self.id
        
        while True:
            # syscall = copy.deepcopy(syscall)
            syscall = self.create_syscall(agent_name, query)
            syscall.set_status("active")
            
            current_time = time.time()
            syscall.set_created_time(current_time)
            syscall.set_response(None)

            if not syscall.get_source():
                syscall.set_source(syscall.agent_name)
            
            if not syscall.get_pid():
                syscall.set_pid(syscall_id)
            
            if isinstance(syscall, LLMSyscall):
                global_llm_req_queue_add_message(syscall)
            elif isinstance(syscall, StorageSyscall):
                global_storage_req_queue_add_message(syscall)
            elif isinstance(syscall, MemorySyscall):
                global_memory_req_queue_add_message(syscall)
            elif isinstance(syscall, ToolSyscall):
                global_tool_req_queue_add_message(syscall)
            
            syscall.start()
            syscall.join()
            
            # breakpoint()

            completed_response = syscall.get_response()
            
            if syscall.get_status() == "done":
                break
            
            # breakpoint()
            
            # Calculate timing metrics
            start_time = syscall.get_start_time()
            end_time = syscall.get_end_time()
            waiting_time = start_time - syscall.get_created_time()
            turnaround_time = end_time - syscall.get_created_time()

            start_times.append(start_time)
            end_times.append(end_time)
            waiting_times.append(waiting_time)
            turnaround_times.append(turnaround_time)

        return {
            "response": completed_response,
            "start_times": start_times,
            "end_times": end_times,
            "waiting_times": waiting_times,
            "turnaround_times": turnaround_times,
        }

    def execute_storage_syscall(self, agent_name: str, query: StorageQuery) -> Dict[str, Any]:
        """
        Execute a storage system call.
        
        Args:
            agent_name: Name of the agent making the request
            query: Storage query to execute
            
        Returns:
            Dict containing response and timing metrics
            
        Example:
            ```python
            query = StorageQuery(operation_type="read", params={"path": "/tmp/file.txt"})
            result = executor.execute_storage_syscall("agent_1", query)
            ```
        """
        # syscall = StorageSyscall(agent_name, query)
        # syscall.set_target("storage")
        # global_storage_req_queue_add_message(syscall)
        return self._execute_syscall(agent_name, query)

    def execute_memory_syscall(self, agent_name: str, query: MemoryQuery) -> Dict[str, Any]:
        """
        Execute a memory system call.
        
        Args:
            agent_name: Name of the agent making the request
            query: Memory query to execute
            
        Returns:
            Dict containing response and timing metrics
            
        Example:
            ```python
            query = MemoryQuery(operation="store", data={"key": "value"})
            result = executor.execute_memory_syscall("agent_1", query)
            ```
        """
        # syscall = Syscall(agent_name, query)
        # syscall.set_target("memory")
        # global_memory_req_queue_add_message(syscall)
        return self._execute_syscall(agent_name, query)

    def execute_tool_syscall(self, agent_name: str, query: ToolQuery) -> Dict[str, Any]:
        """
        Execute a tool system call.
        
        Args:
            agent_name: Name of the agent making the request
            tool_calls: List of tool calls to execute
            
        Returns:
            Dict containing response and timing metrics
            
        Example:
            ```python
            tool_calls = [{"name": "calculator", "arguments": {"operation": "add", "numbers": [1, 2]}}]
            result = executor.execute_tool_syscall("agent_1", tool_calls)
            ```
        """
        # syscall = ToolSyscall(agent_name, tool_calls)
        # syscall.set_target("tool")
        # global_tool_req_queue_add_message(syscall)
        return self._execute_syscall(agent_name, query)

    def execute_llm_syscall(self, agent_name: str, query: LLMQuery) -> Dict[str, Any]:
        """
        Execute an LLM system call.
        
        Args:
            agent_name: Name of the agent making the request
            query: LLM query to execute
            
        Returns:
            Dict containing response and timing metrics
            
        Example:
            ```python
            query = LLMQuery(messages=[{"role": "user", "content": "Hello"}], action_type="chat")
            result = executor.execute_llm_syscall("agent_1", query)
            ```
        """
        # syscall = LLMSyscall(agent_name=agent_name, query=query)
        # syscall.set_target("llm")
        # global_llm_req_queue_add_message(syscall)
        return self._execute_syscall(agent_name, query)

    def execute_file_operation(self, agent_name: str, query: LLMQuery) -> str:
        """
        Execute a file system operation using LLM parsing.
        
        Args:
            agent_name: Name of the agent making the request
            query: LLM query containing file operation instructions
            
        Returns:
            String containing operation summary
            
        Example:
            ```python
            query = LLMQuery(
                messages=[{"role": "user", "content": "Create a file named test.txt"}],
                action_type="operate_file"
            )
            result = executor.execute_file_operation("agent_1", query)
            ```        """
        # Parse file system operation
        system_prompt = "You are a parser for parsing file system operations. Your task is to parse the instructions and return the file system operation call."
        query.messages = [{"role": "system", "content": system_prompt}] + query.messages
        query.tools = storage_syscalls
        
        
        parser_response = self.execute_llm_syscall(agent_name, query)["response"]
        file_operations = parser_response.tool_calls
        
        # breakpoint()
        
        operation_summaries = []
        
        # Execute each file operation
        for operation in file_operations:
            storage_query = StorageQuery(
                operation_type=operation.get("name"),
                params=operation.get("parameters")
            )
            
            # breakpoint()
            storage_response = self.execute_storage_syscall(agent_name, storage_query)
            
            # Summarize operation result
            summary_query = LLMQuery(
                messages=[{
                    "role": "user",
                    "content": f"Tell me what you have done from {storage_response} with a friendly tone. "
                              f"Try to be concise and maintain the key information including file name, file path, etc"
                }],
                action_type="chat"
            )
            summary = self.execute_llm_syscall(agent_name, summary_query)["response"].response_message
            operation_summaries.append(summary)
        
        # Generate final summary
        final_query = LLMQuery(
            messages=[{
                "role": "user",
                "content": f"Tell me what you have done from {json.dumps(operation_summaries)} with a friendly tone. "
                          f"Try to be concise and maintain the key information including file name, file path, etc"
            }],
            action_type="chat"
        )
        
        return self.execute_llm_syscall(agent_name, final_query)["response"].response_message

    def execute_request(self, agent_name: str, query: Any) -> Dict[str, Any]:
        """
        Execute a request based on its type.
        
        Args:
            agent_name: Name of the agent making the request
            query: Query object of various types (LLM, Tool, Memory, Storage)
            
        Returns:
            Dict containing response and timing metrics
            
        Example:
            ```python
            query = LLMQuery(messages=[{"role": "user", "content": "Hello"}], action_type="chat")
            result = executor.execute_request("agent_1", query)
            ```
        """
        if isinstance(query, LLMQuery):
            if query.action_type == "chat" or query.action_type == "chat_with_json_response":
                llm_response = self.execute_llm_syscall(agent_name, query)
                return llm_response
            
            elif query.action_type == "tool_use":
                llm_response = self.execute_llm_syscall(agent_name, query)["response"]
                # breakpoint()
                tool_query = ToolQuery(
                    tool_calls=llm_response.tool_calls,
                    # action_type="tool_use"
                )
                tool_response = self.execute_tool_syscall(agent_name, tool_query)
                # breakpoint()
                return tool_response
            
            elif query.action_type == "operate_file":
                return self.execute_file_operation(agent_name, query)
        elif isinstance(query, ToolQuery):
            return self.execute_tool_syscall(agent_name, query)
        elif isinstance(query, MemoryQuery):
            if query.action_type == "add_agentic_memory":
                metadata = self.execute_memory_content_analyze(agent_name, query)
                query.params.update(metadata)
                # retrieve the related memory and evolve the memory.
                query.action_type = "retrieve_memory"
                similar_memories = self.execute_memory_syscall(agent_name, query)
                query, similar_memories_evolved = self.execute_memory_evolve(query, similar_memories)
                # define a memory abstract in the memory layer.
                query.action_type = "add_memory"
                for memory in similar_memories_evolved:
                    updated_query = MemoryQuery()
                    updated_query.params = memory.return_params() # return a dict with full parameters, also with memory id for updated
                    updated_query.action_type = "update_memory"
                    self.execute_memory_syscall(agent_name, updated_query)
                return self.execute_memory_syscall(agent_name, query)
            elif query.action_type == "add_memory":
                return self.execute_memory_syscall(agent_name, query)
            elif query.action_type == "remove_memory":
                return self.execute_memory_syscall(agent_name, query)
            elif query.action_type == "update_memory":
                return self.execute_memory_syscall(agent_name, query)
            elif query.action_type == "retrieve_memory":
                return self.execute_memory_syscall(agent_name, query)
            elif query.action_type == "get_memory":
                return self.execute_memory_syscall(agent_name, query)
        elif isinstance(query, StorageQuery):
            return self.execute_storage_syscall(agent_name, query)

def create_syscall_executor():
    """
    Create and return a SyscallExecutor instance and its wrapper.
    
    Returns:
        Tuple of (execute_request function, SyscallWrapper class)
        
    Example:
        ```python
        executor, wrapper = create_syscall_executor()
        response = executor("agent_1", LLMQuery(...))
        ```
    """
    executor = SyscallExecutor()
    
    class SyscallWrapper:
        """Wrapper class providing direct access to syscall methods."""
        llm = executor.execute_llm_syscall
        storage = executor.execute_storage_syscall
        memory = executor.execute_memory_syscall
        tool = executor.execute_tool_syscall

    return executor.execute_request, SyscallWrapper

# Maintain backwards compatibility
useSysCall = create_syscall_executor

