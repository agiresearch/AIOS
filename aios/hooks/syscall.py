import time

import json

from typing import List

from aios.core.syscall import Syscall
from aios.core.syscall.llm import LLMSyscall
from aios.core.syscall.storage import StorageSyscall, storage_syscalls
from aios.core.syscall.tool import ToolSyscall
from aios.hooks.stores._global import (
    global_llm_req_queue_add_message,
    global_memory_req_queue_add_message,
    global_storage_req_queue_add_message,
    global_tool_req_queue_add_message,
)

from cerebrum.llm.communication import LLMQuery
from cerebrum.memory.communication import MemoryQuery
from cerebrum.storage.communication import StorageQuery
from cerebrum.tool.communication import ToolQuery

def useSysCall():
    def storage_syscall_exec(agent_name, query):
        
        syscall = StorageSyscall(agent_name, query)
        syscall.set_status("active")
        
        # breakpoint()

        completed_response, start_times, end_times, waiting_times, turnaround_times = (
            "",
            [],
            [],
            [],
            [],
        )
        while syscall.get_status() != "done":
            current_time = time.time()
            syscall.set_created_time(current_time)
            syscall.set_response(None)

            global_storage_req_queue_add_message(syscall)

            syscall.start()
            syscall.join()

            completed_response = syscall.get_response()

            if syscall.get_status() != "done":
                pass
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


    def mem_syscall_exec(agent_name, query):
        syscall = Syscall(agent_name, query)
        syscall.set_status("active")

        completed_response, start_times, end_times, waiting_times, turnaround_times = (
            "",
            [],
            [],
            [],
            [],
        )
        while syscall.get_status() != "done":
            current_time = time.time()
            syscall.set_created_time(current_time)
            syscall.set_response(None)

            global_memory_req_queue_add_message(syscall)

            syscall.start()
            syscall.join()

            completed_response = syscall.get_response()

            if syscall.get_status() != "done":
                pass
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


    def tool_syscall_exec(agent_name, tool_calls):
        syscall = ToolSyscall(agent_name, tool_calls)
        syscall.set_status("active")

        completed_response, start_times, end_times, waiting_times, turnaround_times = (
            "",
            [],
            [],
            [],
            [],
        )
        while syscall.get_status() != "done":
            current_time = time.time()
            syscall.set_created_time(current_time)
            syscall.set_response(None)

            global_tool_req_queue_add_message(syscall)

            syscall.start()
            syscall.join()

            completed_response = syscall.get_response()

            if syscall.get_status() != "done":
                pass
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


    def llm_syscall_exec(agent_name, query):
        syscall = LLMSyscall(agent_name=agent_name, query=query)

        syscall.set_status("active")

        completed_response, start_times, end_times, waiting_times, turnaround_times = (
            "",
            [],
            [],
            [],
            [],
        )

        while syscall.get_status() != "done":
            current_time = time.time()
            syscall.set_created_time(current_time)
            syscall.set_response(None)

            global_llm_req_queue_add_message(syscall)

            syscall.start()
            syscall.join()

            completed_response = syscall.get_response()

            if syscall.get_status() != "done":
                pass
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


    def send_request(agent_name, query):
        if isinstance(query, LLMQuery):
            action_type = query.action_type
            # print(action_type)
            if action_type == "chat":
                return llm_syscall_exec(agent_name, query)

            elif action_type == "tool_use":
                response = llm_syscall_exec(agent_name, query)["response"]
                tool_calls = response.tool_calls
                return tool_syscall_exec(agent_name, tool_calls)

            elif action_type == "operate_file":
                # parse the file system operation
                system_prompt = "You are a parser for parsing file system operations. Your task is to parse the instructions and return the file system operation call."
                query.messages = [{"role": "system", "content": system_prompt}] + query.messages
                query.tools = storage_syscalls
                
                parser_response = llm_syscall_exec(agent_name, query)["response"]
                file_operations = parser_response.tool_calls
                file_operation_messages = []
                
                # execute the file system operation
                for file_operation in file_operations:
                    
                    if not isinstance(file_operation, List):
                        file_operation = [file_operation]
                        
                    storage_query = StorageQuery(
                        messages=file_operation
                    )
                    
                    storage_response = storage_syscall_exec(agent_name, storage_query)
                    summarization_query = LLMQuery(
                        messages=[
                            {"role": "system", "content": "You are a summarizer for summarizing the results. Try to maintain the key information including file name, file path, etc"},
                            {"role": "user", "content": f"Describe what you have done about the file operations of {storage_response} with a friendly tone"}
                        ],
                        action_type="chat"
                    )
                    
                    summarization_response = llm_syscall_exec(agent_name, summarization_query)["response"].response_message
                    file_operation_messages.append(summarization_response)
                
                # summarize the results of the file system operation
                final_query = LLMQuery(
                    messages=[
                        {"role": "user", "content": f"Summarize what you have done based on your file operations: {json.dumps(file_operation_messages)} with a friendly tone"}
                    ],
                    action_type="chat"
                )
                
                final_response = llm_syscall_exec(agent_name, final_query)["response"].response_message
                
                return summarization_response

        elif isinstance(query, ToolQuery):
            return tool_syscall_exec(agent_name, query)

        elif isinstance(query, MemoryQuery):
            return mem_syscall_exec(agent_name, query)

        elif isinstance(query, StorageQuery):
            return storage_syscall_exec(agent_name, query)

    class SysCallWrapper:
        llm = llm_syscall_exec
        storage = storage_syscall_exec
        memory = memoryview
        tool = tool_syscall_exec

    return send_request, SysCallWrapper
