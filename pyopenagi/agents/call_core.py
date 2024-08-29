import time
from threading import Thread

from aios.hooks.stores._global import global_llm_req_queue_add_message
from .agent_process import AgentProcess
from ..utils.logger import AgentLogger


class CustomizedThread(Thread):
    def __init__(self, target, args=()):
        super().__init__()
        self.target = target
        self.args = args
        self.result = None

    def run(self):
        self.result = self.target(*self.args)

    def join(self):
        super().join()
        return self.result


class CallCore:
    """
    Simplify BaseAgent to provide an interface for external frameworks to make LLM requests using aios.
    """
    def __init__(self,
                 agent_name,
                 agent_process_factory,
                 log_mode: str = "console"
                 ):
        self.agent_name = agent_name
        self.agent_process_factory = agent_process_factory
        self.log_mode = log_mode
        self.logger = self.setup_logger()

    # the default method used for getting response from AIOS
    def get_response(self,
                     query,
                     temperature=0.0
                     ):

        thread = CustomizedThread(target=self.query_loop, args=(query,))
        thread.start()
        return thread.join()

    def query_loop(self, query):
        agent_process = self.create_agent_request(query)

        completed_response, start_times, end_times, waiting_times, turnaround_times = "", [], [], [], []

        while agent_process.get_status() != "done":
            thread = Thread(target=self.listen, args=(agent_process,))
            current_time = time.time()
            # reinitialize agent status
            agent_process.set_created_time(current_time)
            agent_process.set_response(None)

            global_llm_req_queue_add_message(agent_process)

            # LLMRequestQueue.add_message(agent_process)

            thread.start()
            thread.join()

            completed_response = agent_process.get_response()
            if agent_process.get_status() != "done":
                self.logger.log(
                    f"Suspended due to the reach of time limit ({agent_process.get_time_limit()}s). Current result is: {completed_response.response_message}\n",
                    level="suspending"
                )
            start_time = agent_process.get_start_time()
            end_time = agent_process.get_end_time()
            waiting_time = start_time - agent_process.get_created_time()
            turnaround_time = end_time - agent_process.get_created_time()

            start_times.append(start_time)
            end_times.append(end_time)
            waiting_times.append(waiting_time)
            turnaround_times.append(turnaround_time)
            # Re-start the thread if not done

        # self.agent_process_factory.deactivate_agent_process(agent_process.get_pid())

        return completed_response, start_times, end_times, waiting_times, turnaround_times

    def create_agent_request(self, query):
        agent_process = self.agent_process_factory.activate_agent_process(
            agent_name=self.agent_name,
            query=query
        )
        agent_process.set_created_time(time.time())
        # print("Already put into the queue")
        return agent_process

    def listen(self, agent_process: AgentProcess):
        """Response Listener for agent

        Args:
            agent_process (AgentProcess): Listened AgentProcess

        Returns:
            str: LLM response of Agent Process
        """
        while agent_process.get_response() is None:
            time.sleep(0.2)

        return agent_process.get_response()

    def setup_logger(self):
        logger = AgentLogger(self.agent_name, self.log_mode)
        return logger
