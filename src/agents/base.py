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
        self.logger.info(f"[{agent_name}]" + " has been initialized.")

        self.set_status("active")
        self.set_created_time(time)

    def run(self):
        '''Execute each step to finish the task.'''
        pass

    def setup_logger(self):
        logger = logging.getLogger(f"{self.agent_name} Logger")
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

    def load_config(self):
        config_file = os.path.join(os.getcwd(), "src", "agents", "agent_config/{}.json".format(self.agent_name))
        with open(config_file, "r") as f:
            config = json.load(f)
            return config

    def get_response(self, prompt, temperature=0.0):
        agent_process = self.agent_process_factory.activate_agent_process(
            agent_name = self.agent_name,
            prompt = prompt
        )
        agent_process.set_created_time(time.time())
        # print("Already put into the queue")
        self.agent_process_queue.put(agent_process)
        thread = CustomizedThread(target=self.listen, args=(agent_process,))
        thread.start()
        # print(result)
        result = thread.join()
        waiting_time = agent_process.get_start_time() - agent_process.get_created_time()
        turnaround_time = agent_process.get_end_time() - agent_process.get_created_time()
        result = result.replace("\n", "")
        return result, waiting_time, turnaround_time

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


    def get_final_result(self, prompt):
        prompt = f"Given the interaction history: {prompt}, give the answer to the task input and don't be verbose!"
        final_result, waiting_time, turnaround_time = self.get_response(prompt)
        final_result.replace("\n", "")
        return final_result, waiting_time, turnaround_time

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
