# base implementation of the scheduler, sets up the threads and init
# which all sub classes will inherit and wouldn't need to change.

from threading import Thread

from aios.llm_core.llms import LLMKernel

from aios.utils.logger import SchedulerLogger
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
