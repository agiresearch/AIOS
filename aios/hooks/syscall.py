from threading import Thread, Lock, Event
from typing import Mapping

import random
import time
from aios.hooks.stores._global import global_llm_req_queue_add_message


class Syscall(Thread):
    def __init__(self, agent_name, query):
        """Agent Process

        Args:
            agent_name (str): Name of the agent
            query (Query): Query sent by the agent
        """
        super().__init__(name=agent_name)
        self.agent_name = agent_name
        self.query = query
        self.event = Event()
        self.pid: int = None
        self.status = None
        self.response = None
        self.time_limit = None
        self.created_time = None
        self.start_time = None
        self.end_time = None

    def set_created_time(self, time):
        self.created_time = time

    def get_created_time(self):
        return self.created_time

    def set_start_time(self, time):
        self.start_time = time

    def get_start_time(self):
        return self.start_time

    def set_end_time(self, time):
        self.end_time = time

    def get_end_time(self):
        return self.end_time

    def set_priority(self, priority):
        self.priority = priority

    def get_priority(self):
        return self.priority

    def set_status(self, status):
        self.status = status

    def get_status(self):
        return self.status

    def set_aid(self, aid):
        self.aid = aid

    def get_aid(self):
        return self.pid

    def set_pid(self, pid):
        self.pid = pid

    def get_pid(self):
        return self.pid

    def get_response(self):
        return self.response

    def set_response(self, response):
        self.response = response

    def get_time_limit(self):
        return self.time_limit

    def set_time_limit(self, time_limit):
        self.time_limit = time_limit

    def run(self):
        """Response Listener for agent

        Args:
            agent_process (AgentProcess): Listened AgentProcess

        Returns:
            str: LLM response of Agent Process
        """
        self.set_pid(self.native_id)
        self.event.wait()


class LLMSyscall(Syscall):
    pass


class MemSyscall(Syscall):
    pass


class StorageSyscall(Syscall):
    pass


def send_request(agent_name, query):
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

    return (
        completed_response,
        start_times,
        end_times,
        waiting_times,
        turnaround_times,
    )
