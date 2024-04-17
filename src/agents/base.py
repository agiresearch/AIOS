import os

import json

from src.agents.agent_process import (
    AgentProcess,
    # AgentProcessQueue
)

# from multiprocessing import Process

import logging

import time

from threading import Thread

from datetime import datetime

import numpy as np

from src.utils.logger import AgentLogger
class CustomizedThread(Thread):
    def __init__(self, target, args=()):
        super().__init__()
        self.target = target
        self.args = args
        self.result = None

    def run(self):
        self.result = self.target(*self.args)

    def join(self):
        super().join()
        return self.result

# class CustomizedProcess(Process):
#     def __init__(self, target, args=()):
#         super().__init__()
#         self.target = target
#         self.args = args
#         self.result = None

#     def run(self):
#         self.result = self.target(*self.args)

#     def join(self):
#         super().join()
#         return self.result

class BaseAgent:
    def __init__(self,
                 agent_name,
                 task_input,
                 llm,
                 agent_process_queue,
                 agent_process_factory,
                 log_mode: str
        ):
        self.agent_name = agent_name
        self.config = self.load_config()
        self.prefix = " ".join(self.config["description"])
        self.task_input = task_input
        self.llm = llm
        self.agent_process_queue = agent_process_queue
        self.agent_process_factory = agent_process_factory

        self.log_mode = log_mode
        self.logger = self.setup_logger()
        self.logger.log(f"Initialized. \n", level="info")

        self.set_status("active")
        self.set_created_time(time)

    def run(self):
        '''Execute each step to finish the task.'''
        pass

    def setup_logger(self):
        logger = AgentLogger(self.agent_name, self.log_mode)
        return logger

    def load_config(self):
        config_file = os.path.join(os.getcwd(), "src", "agents", "agent_config/{}.json".format(self.agent_name))
        with open(config_file, "r") as f:
            config = json.load(f)
            return config

    def get_response(self, prompt, temperature=0.0):
        thread = CustomizedThread(target=self.query_loop, args=(prompt, ))
        thread.start()
        return thread.join()
        # process = CustomizedProcess(target=self.query_loop, args=(prompt, ))
        # process.start()
        # return process.join()
        # return self.query_loop(prompt)

    def query_loop(self, prompt):
        agent_process = self.create_agent_request(prompt)

        # print(f"Loop Prompt: {prompt}")
        completed_response, waiting_times, turnaround_times = "", [], []

        # print("Already put into the queue")
        while agent_process.get_status() != "done":
            # print(agent_process.get_status())
            thread = Thread(target=self.listen, args=(agent_process, ))
            # process = Process(target=self.listen, args=(agent_process, ))
            current_time = time.time()

            # reinitialize agent status
            agent_process.set_created_time(current_time)
            agent_process.set_response(None)
            self.agent_process_queue.put(agent_process)

            thread.start()
            thread.join()
            # process.start()
            # process.join()

            completed_response = agent_process.get_response()
            if agent_process.get_status() != "done":
                self.logger.log(
                    f"Suspended due to the reach of time limit ({agent_process.get_time_limit()}s). Current result is: {completed_response}\n",
                    level="suspending"
                )

            waiting_time = agent_process.get_start_time() - current_time
            turnaround_time = agent_process.get_end_time() - current_time

            waiting_times.append(waiting_time)
            turnaround_times.append(turnaround_time)
            # Re-start the thread if not done

        self.agent_process_factory.deactivate_agent_process(agent_process.get_pid())

        completed_response = completed_response.replace("\n", "")
        return completed_response, np.mean(np.array(waiting_times)), np.mean(np.array(turnaround_times))

    def create_agent_request(self, prompt):
        agent_process = self.agent_process_factory.activate_agent_process(
            agent_name = self.agent_name,
            prompt = prompt
        )
        agent_process.set_created_time(time.time())
        # print("Already put into the queue")
        return agent_process

    def listen(self, agent_process):
        """Response Listener for agent

        Args:
            agent_process (AgentProcess): Listened AgentProcess

        Returns:
            str: LLM response of Agent Process
        """
        while agent_process.get_response() is None:
            time.sleep(0.2)

        return agent_process.get_response()

    def set_aid(self, aid):
        self.aid = aid

    def get_aid(self):
        return self.aid

    def get_agent_name(self):
        return self.agent_name

    def set_status(self, status):

        """
        Status type: Waiting, Running, Done, Inactive
        """
        self.status = status

    def get_status(self):
        return self.status

    def set_created_time(self, time):
        self.created_time = time

    def get_created_time(self):
        return self.created_time

    def parse_result(self, prompt):
        pass
