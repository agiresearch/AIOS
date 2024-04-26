import click

import os

from datetime import datetime

class BaseLogger:
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
            "execute": "green",
            "suspend": "yellow",
            "info": "white"
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
