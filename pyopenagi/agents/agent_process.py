import heapq

from threading import Thread, Lock, Event

from ..utils.chat_template import Query

class AgentProcess:
    def __init__(self,
            agent_name: str,
            query: Query
        ):
        """Agent Process

        Args:
            agent_name (str): Name of the agent
            query (Query): Query sent by the agent
        """
        self.agent_name = agent_name
        self.query = query
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


class LLMRequestProcess(AgentProcess):
    pass

class AgentProcessFactory:
    def __init__(self, agent_process_log_mode = None):
        self.max_pid = 1024
        self.pid_pool = [i for i in range(self.max_pid)]
        heapq.heapify(self.pid_pool)

        self.thread = Thread(target=self.deactivate_agent_process)

        self.current_agent_processes = dict()

        self.current_agent_processes_lock = Lock()

        self.terminate_signal = Event()

        self.agent_process_log_mode = agent_process_log_mode

    def activate_agent_process(self, agent_name, query):
        if not self.terminate_signal.is_set():
            with self.current_agent_processes_lock:
                agent_process = AgentProcess(
                    agent_name = agent_name,
                    query = query
                )
                pid = heapq.heappop(self.pid_pool)
                agent_process.set_pid(pid)
                agent_process.set_status("active")
                self.current_agent_processes[pid] = agent_process
                return agent_process

    def print_agent_process(self):
        headers = ["Agent Process ID", "Agent Name", "Created Time", "Status"]
        data = []
        for id, agent_process in self.current_agent_processes.items():
            agent_name = agent_process.agent_name
            created_time = agent_process.created_time
            status = agent_process.status
            # memory_usage = f"{asizeof.asizeof(agent)} bytes"
            data.append(
                [id, agent_name, created_time, status]
            )
        self.print(headers=headers, data=data)


    def print(self, headers, data):
        # align output
        column_widths = [
            max(len(str(row[i])) for row in [headers] + data) for i in range(len(headers))
        ]
        print("+" + "-" * (sum(column_widths) + len(headers) * 3 - 3 ) + "+")
        print(self.format_row(headers, column_widths))
        print("=" * (sum(column_widths) + len(headers) * 3 - 1))
        for i, row in enumerate(data):
            print(self.format_row(row, column_widths))
            if i < len(data):
                print("-" * (sum(column_widths) + len(headers) * 3 - 1))
        print("+" + "-" * (sum(column_widths) + len(headers) * 3 - 3 ) + "+")


    def format_row(self, row, widths, align="<"):
        row_str = " | ".join(f"{str(item):{align}{widths[i]}}" for i, item in enumerate(row))
        return row_str

    def deactivate_agent_process(self, pid):
        self.current_agent_processes.pop(pid)
        heapq.heappush(self.pid_pool, pid)

    def start(self):
        """start the factory to check inactive agent"""
        self.thread.start()

    def stop(self):
        self.thread.join()
