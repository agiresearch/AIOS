from queue import Queue, Empty
from threading import Thread

import logging

from src.agents.agent_process import AgentProcess

import time

from datetime import datetime

import os
class BaseScheduler:
    def __init__(self, llm, log_mode):
        self.active = False # start/stop the scheduler
        self.log_mode = log_mode
        self.logger = self.setup_logger()
        self.thread = Thread(target=self.run)
        self.llm = llm

    def run(self):
        pass

    def start(self):
        """start the scheduler"""
        self.active = True
        self.thread.start()

    def setup_logger(self):
        logger = logging.getLogger(f"FIFO Scheduler Logger")
        # logger.setLevel(logging.INFO)  # Set the minimum logging level
        date_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        # Provide two log modes: console and file
        # Ensure the logger doesn't propagate to the root logger
        logger.propagate = False

        # Remove all handlers associated with this logger
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)

        if self.log_mode == "console":
            handler = logging.StreamHandler()
            handler.setLevel(logging.INFO)  # Set logging level for console output
        else:
            assert self.log_mode == "file"
            log_dir = os.path.join(os.getcwd(), "logs", "scheduler")
            if not os.path.exists(log_dir):
                os.makedirs(log_dir)
            log_file = os.path.join(log_dir, f"{date_time}.txt")
            handler = logging.FileHandler(log_file)
            handler.setLevel(logging.INFO)  # Set logging

        logger.addHandler(handler) # enabled when run in a simulated shell
        return logger

    def stop(self):
        """stop the scheduler"""
        self.active = False
        self.thread.join()

    def execute_request(self, agent_process: AgentProcess):
        agent_process.set_status("Executing")
        self.logger.info(f"[{agent_process.agent_name}] is executing.")
        agent_process.set_start_time(time.time())
        response = self.llm.address_request(agent_process.prompt)
        agent_process.set_response(response)
        agent_process.set_end_time(time.time())
        agent_process.set_status("Done")
