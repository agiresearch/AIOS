import os

import json

from src.agents.agent_process import (
    AgentProcess,
    # AgentProcessQueue
)

import logging

import time

from threading import Thread

from datetime import datetime

import numpy as np

class CustomizedThread(Thread):
    def run(self):
        if self._target is not None:
            self._return = self._target(*self._args, **self._kwargs)

    def join(self):
        super().join()
        return self._return

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
        self.logger.info(f"Initialized. \n")

        self.set_status("active")
        self.set_created_time(time)

    def run(self):
        '''Execute each step to finish the task.'''
        pass

    def setup_logger(self):
        logger = logging.getLogger(f"{self.agent_name}")
        logger.setLevel(logging.INFO)  # Set the minimum logging level
        # logger.disabled = True
        date_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        # Provide two log modes: console and file

        # Ensure the logger doesn't propagate to the root logger
        logger.propagate = False

        # Remove all handlers associated with this logger
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)

        if self.log_mode == "console":
            # logger.disabled = False
            handler = logging.StreamHandler()
            handler.setLevel(logging.INFO)  # Set logging level for console output
            handler.setFormatter(self.CustomFormatter())
        else:
            assert self.log_mode == "file"
            # logger.disabled = False
            log_dir = os.path.join(os.getcwd(), "logs", "agents",
                                    f"{self.agent_name}")
            if not os.path.exists(log_dir):
                os.makedirs(log_dir)
            log_file = os.path.join(log_dir, f"{date_time}.txt")
            handler = logging.FileHandler(log_file)
            handler.setLevel(logging.INFO)  # Set logging

        logger.addHandler(handler) # enabled when run in a simulated shell
        return logger
    class CustomFormatter(logging.Formatter):
        """Logging Formatter to add colors and count warning / errors"""

        grey = "\x1b[38;21m"
        green = "\x1b[32;1m"
        yellow = "\x1b[33;1m"
        red = "\x1b[31;1m"
        bold_red = "\x1b[31;1m"
        bold_blue = "\033[1;34m"
        reset = "\x1b[0m"
        format = "[%(name)s]: %(message)s"

        FORMATS = {
            # logging.DEBUG: grey + format + reset,
            logging.INFO: grey + format + reset,
            # logging.WARNING: yellow + format + reset,
            # logging.ERROR: red + format + reset,
            # logging.CRITICAL: bold_red + format + reset
        }

        def format(self, record):
            log_fmt = self.FORMATS.get(record.levelno)
            formatter = logging.Formatter(log_fmt)
            return formatter.format(record)

    def load_config(self):
        config_file = os.path.join(os.getcwd(), "src", "agents", "agent_config/{}.json".format(self.agent_name))
        with open(config_file, "r") as f:
            config = json.load(f)
            return config

    def get_response(self, prompt, temperature=0.0):
        thread = CustomizedThread(target=self.query_loop, args=(prompt,))
        thread.start()
        return thread.join()
        # return self.query_loop(prompt)

    def query_loop(self, prompt):
        agent_process = self.create_agent_request(prompt)
        completed_response, waiting_times, turnaround_times = "", [], []

        # print("Already put into the queue")
        while agent_process.get_status() != "done":
            # print(agent_process.get_status())
            thread = Thread(target=self.listen, args=(agent_process,))
            current_time = time.time()

            # reinitialize agent status
            agent_process.set_created_time(current_time)
            agent_process.set_response(None)
            self.agent_process_queue.put(agent_process)

            thread.start()
            thread.join()

            completed_response = agent_process.get_response()
            waiting_time = agent_process.get_start_time() - current_time
            turnaround_time = agent_process.get_end_time() - current_time

            waiting_times.append(waiting_time)
            turnaround_times.append(turnaround_time)
            # Re-start the thread if not done


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
