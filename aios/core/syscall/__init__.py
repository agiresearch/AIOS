
from threading import Event, Thread

from cerebrum.llm.communication import Request


class Syscall(Thread):
    def __init__(self, agent_name, query: Request):
        super().__init__()
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
        self.set_pid(self.native_id)
        self.event.wait()

