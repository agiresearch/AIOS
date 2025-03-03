# This file contains utilities for logging which are used in the simulator.py
# file and related sections for logging the scheduler and agents's outputs
# Each subclass overrides the load_log_file method depending on its use case
# TODO: support stdout and stderr logging

# alternative to argparse used due to its inconsistencies
import click

import os

from datetime import datetime

class BaseLogger:
    """ stub implementation of logging utilities """

    def __init__(self,
            logger_name,
            log_mode = "console",
        ) -> None:
        self.logger_name = logger_name
        self.log_mode = log_mode
        self.log_file = self.load_log_file() if log_mode == "file" else None

        self.level_color = dict()

    def log(self, content, level):
        if self.log_mode == "console":
            self.log_to_console(content, level)
        else:
            assert self.log_mode == "file" and self.log_file is not None
            self.log_to_file(content, self.log_file)

    # each subclass should override this
    def load_log_file(self):
        pass

    def log_to_console(self, content, level):
        # print(content)
        click.secho(f"[{self.logger_name}] " + content, fg=self.level_color[level])

    def log_to_file(self, content, log_file):
        with open(log_file, "a") as w:
            w.writelines(content)

class SchedulerLogger(BaseLogger):
    def __init__(self, logger_name, log_mode="console") -> None:
        super().__init__(logger_name, log_mode)
        self.level_color = {
            "executing": "green",
            "suspending": "yellow",
            "info": "white",
            "done": "blue"
        }

    def load_log_file(self):
        date_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_dir = os.path.join(os.getcwd(), "logs", "scheduler")
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
        log_file = os.path.join(log_dir, f"{date_time}.txt")
        return log_file


class AgentLogger(BaseLogger):
    def __init__(self, logger_name, log_mode="console") -> None:
        super().__init__(logger_name, log_mode)
        self.level_color = {
            "info": (248, 246, 227), # white
            "executing": (217, 237, 191), # green
            "suspending": (255, 235, 178), # yellow
            "done": (122, 162, 227) # blue
        }

    def load_log_file(self):
        date_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_dir = os.path.join(os.getcwd(), "logs", "agents", self.logger_name)
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
        log_file = os.path.join(log_dir, f"{date_time}.txt")
        return log_file


class LLMKernelLogger(BaseLogger):
    def __init__(self, logger_name, log_mode="console") -> None:
        super().__init__(logger_name, log_mode)
        self.level_color = {
            "info": (246, 245, 242),
            "executing": (65, 176, 110), # green
            "suspending": (255, 201, 74), # yellow
            "done": (122, 162, 227) # blue
        }

    def log_to_console(self, content, level):
        # print(content)
        click.secho(f"[\U0001F916{self.logger_name}] " + content, fg=self.level_color[level], bold=True)

    def load_log_file(self):
        date_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_dir = os.path.join(os.getcwd(), "logs", "llm_kernel", self.logger_name)
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
        log_file = os.path.join(log_dir, f"{date_time}.txt")
        return log_file

class SDKLogger(BaseLogger):
    def __init__(self, logger_name, log_mode="console") -> None:
        super().__init__(logger_name, log_mode)
        self.level_color = {
            "info": (248, 246, 227), # white
            "warn": (255, 201, 74), # yellow
            "error": (255, 0, 0), # red
        }

    def load_log_file(self):
        date_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_dir = os.path.join(os.getcwd(), "logs", "agents", self.logger_name)
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
        log_file = os.path.join(log_dir, f"{date_time}.txt")
        return log_file
