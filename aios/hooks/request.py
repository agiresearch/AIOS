from threading import Thread, Lock, Event
from typing import Mapping

import random
import time
from aios.hooks.stores._global import (
    global_llm_req_queue_add_message,
    global_memory_req_queue_add_message,
)


class AgentRequest(Thread):
    def __init__(self, agent_name, request_data):
        """Agent Process

        Args:
            agent_name (str): Name of the agent
            query (Query): Query sent by the agent
        """
        super().__init__(name=agent_name)
        self.agent_name = agent_name
        self.request_data = request_data
        self.event = Event()
        self.pid = None
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


class LLMRequest(AgentRequest):
    pass


def send_request(agent_name, query):
    if query.action_type == "message_llm":
        # retrive memory
        llm_response, _, _, _, _ = call_llm(
            agent_name=agent_name, request_data=query
        )  # chat with llm
        return (llm_response, _, _, _, _)
        # save memory

    elif query.action_type == "call_tool":
        # retrive memory
        llm_response, _, _, _, _ = call_llm(
            agent_name=agent_name, request_data=query
        )  # chat with llm
        return (llm_response, _, _, _, _)

    elif query.action_type == "operate_file":
        pass


def call_llm(agent_name, request_data):
    agent_request = AgentRequest(agent_name=agent_name, request_data=request_data)
    agent_request.set_status("active")

    completed_response, start_times, end_times, waiting_times, turnaround_times = (
        "",
        [],
        [],
        [],
        [],
    )
    # completed_response = ""

    while agent_request.get_status() != "done":
        current_time = time.time()
        agent_request.set_created_time(current_time)
        agent_request.set_response(None)

        global_llm_req_queue_add_message(agent_request)

        agent_request.start()
        agent_request.join()

        completed_response = agent_request.get_response()

        if agent_request.get_status() != "done":
            pass

        start_time = agent_request.get_start_time()
        end_time = agent_request.get_end_time()
        waiting_time = start_time - agent_request.get_created_time()
        turnaround_time = end_time - agent_request.get_created_time()

        start_times.append(start_time)
        end_times.append(end_time)
        waiting_times.append(waiting_time)
        turnaround_times.append(turnaround_time)

    # return completed_response
    return (
        completed_response,
        start_times,
        end_times,
        waiting_times,
        turnaround_times,
    )


def call_memory(agent_name, request_data):
    agent_request = AgentRequest(agent_name=agent_name, request_data=request_data)
    agent_request.set_status("active")

    completed_response, start_times, end_times, waiting_times, turnaround_times = (
        "",
        [],
        [],
        [],
        [],
    )
    # completed_response = ""

    while agent_request.get_status() != "done":
        current_time = time.time()
        agent_request.set_created_time(current_time)
        agent_request.set_response(None)

        global_memory_req_queue_add_message(agent_request)

        agent_request.start()
        agent_request.join()

        completed_response = agent_request.get_response()

        if agent_request.get_status() != "done":
            pass

        start_time = agent_request.get_start_time()
        end_time = agent_request.get_end_time()
        waiting_time = start_time - agent_request.get_created_time()
        turnaround_time = end_time - agent_request.get_created_time()

        start_times.append(start_time)
        end_times.append(end_time)
        waiting_times.append(waiting_time)
        turnaround_times.append(turnaround_time)

    # return completed_response
    return (
        completed_response,
        start_times,
        end_times,
        waiting_times,
        turnaround_times,
    )
