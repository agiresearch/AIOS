from datetime import datetime

import heapq

from .native_agents.math_agent.math_agent import MathAgent

from .native_agents.narrative_agent.narrative_agent import NarrativeAgent

from .native_agents.rec_agent.rec_agent import RecAgent

from concurrent.futures import ThreadPoolExecutor, as_completed

from threading import Thread, Lock, Event

# from multiprocessing import Process, Lock, Event

from pympler import asizeof

class AgentFactory:
    def __init__(self, llm, agent_process_queue, agent_process_factory, agent_log_mode):
        self.max_aid = 256
        self.llm = llm
        self.aid_pool = [i for i in range(self.max_aid)]
        heapq.heapify(self.aid_pool)
        self.agent_process_queue = agent_process_queue
        self.agent_process_factory = agent_process_factory

        self.agent_table = {
            "MathAgent": MathAgent,
            "NarrativeAgent": NarrativeAgent,
            "RecAgent": RecAgent,
            # "TravelAgent": TravelAgent
        }

        self.current_agents = {}

        self.current_agents_lock = Lock()

        # self.thread = Thread(target=self.deactivate_agent)

        self.terminate_signal = Event()

        self.agent_log_mode = agent_log_mode

    def activate_agent(self, agent_name, task_input):
        # print(task_input)
        agent = self.agent_table[agent_name](
            agent_name = agent_name,
            task_input = task_input,
            llm = self.llm,
            agent_process_queue = self.agent_process_queue,
            agent_process_factory = self.agent_process_factory,
            log_mode = self.agent_log_mode
        )
        aid = heapq.heappop(self.aid_pool)

        agent.set_aid(aid)
        time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        agent.set_status("active")
        agent.set_created_time(time)
        if not self.terminate_signal.is_set():
            with self.current_agents_lock:
                self.current_agents[aid] = agent

        return agent

    def run_agent(self, agent_name, task_input):
        agent = self.activate_agent(
            agent_name=agent_name,
            task_input=task_input
        )
        # print(task_input)
        agent.run()
        self.deactivate_agent(agent.get_aid())

    def print_agent(self):
        headers = ["Agent ID", "Agent Name", "Created Time", "Status", "Memory Usage"]
        data = []
        for id, agent in self.current_agents.items():
            agent_name = agent.agent_name
            created_time = agent.created_time
            status = agent.status
            memory_usage = f"{asizeof.asizeof(agent)} bytes"
            data.append(
                [id, agent_name, created_time, status, memory_usage]
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

    def deactivate_agent(self, aid):
        self.current_agents.pop(aid)
        heapq.heappush(self.aid_pool, aid)

    def start(self):
        """start the factory to check inactive agent"""
        self.thread.start()

    def stop(self):
        self.thread.join()
