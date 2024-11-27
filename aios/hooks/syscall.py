import time

from aios.core.syscall import Syscall
from aios.core.syscall.llm import LLMSyscall
from aios.core.syscall.storage import StorageSyscall
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
                # print(response)
                tool_calls = response.tool_calls
                # print(tool_calls)
                return tool_syscall_exec(agent_name, tool_calls)

            elif action_type == "operate_file":
                return storage_syscall_exec(llm_syscall_exec(agent_name, query))

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
