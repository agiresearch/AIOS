from queue import Queue, Empty
from threading import Thread

import logging

from src.llms.llms import LLMKernel

import time

from datetime import datetime

import os
class BaseScheduler:
    def __init__(self, llm: LLMKernel, log_mode):
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
        logger = logging.getLogger(f"Scheduler")
        logger.setLevel(logging.INFO)  # Set the minimum logging level
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
            handler.setFormatter(self.CustomFormatter())
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
            logging.INFO: green + format + reset,
            # logging.WARNING: yellow + format + reset,
            # logging.ERROR: red + format + reset,
            # logging.CRITICAL: bold_red + format + reset
        }

        def format(self, record):
            log_fmt = self.FORMATS.get(record.levelno)
            formatter = logging.Formatter(log_fmt)
            return formatter.format(record)

    def stop(self):
        """stop the scheduler"""
        self.active = False
        self.thread.join()

    def execute_request(self, agent_process):
        pass
