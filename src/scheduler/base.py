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
class BaseScheduler(multiprocessing.Process):
    def __init__(self, llm: LLMKernel, agent_process_queue, llm_request_responses, log_mode):
        super().__init__()
        # self.active = False # start/stop the scheduler
        self.log_mode = log_mode
        self.logger = self.setup_logger()
        self.agent_process_queue = agent_process_queue
        self.llm_request_responses = llm_request_responses
        # self.thread = Thread(target=self.run)
        # self.process = Process(target=self.run)
        self.llm = llm

    def run(self):
        pass

    # def start(self):
    #     """start the scheduler"""
    #     self.active = True
    #     # self.thread.start()
    #     self.process.start()

    def setup_logger(self):
        logger = SchedulerLogger("Scheduler", self.log_mode)
        return logger

    # def stop(self):
    #     """stop the scheduler"""
    #     self.active = False
    #     # self.thread.join()
    #     self.process.terminate()

    def execute_request(self, llm_request):
        pass
