from queue import Queue, Empty
from threading import Thread

import logging

from src.llm_kernel.llms import LLMKernel

import time

from datetime import datetime

import os

from src.utils.logger import SchedulerLogger

from multiprocessing import Process

import multiprocessing

# multiprocessing.set_start_method('spawn', force=True)

import threading
class BaseScheduler(multiprocessing.Process):
    def __init__(self, llm: LLMKernel, agent_process_queue, llm_request_responses, log_mode):
        super().__init__()
        self.log_mode = log_mode
        self.logger = self.setup_logger()
        self.agent_process_queue = agent_process_queue
        self.llm_request_responses = llm_request_responses
        self.llm = llm

    def run(self):
        pass

    def setup_logger(self):
        logger = SchedulerLogger("Scheduler", self.log_mode)
        return logger

    def execute_request(self, llm_request):
        pass
