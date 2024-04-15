from queue import Queue, Empty
from threading import Thread

import logging

from src.llm_kernel.llms import LLMKernel

import time

from datetime import datetime

import os

from src.utils.logger import SchedulerLogger
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
        logger = SchedulerLogger("Scheduler", self.log_mode)
        return logger

    def stop(self):
        """stop the scheduler"""
        self.active = False
        self.thread.join()

    def execute_request(self, agent_process):
        pass
