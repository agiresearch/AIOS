from queue import Queue, Empty
from threading import Thread

class BaseScheduler:
    def __init__(self, llm):
        # self.agent_process_queue = Queue()
        # # start/stop the scheduler
        # self.active = False
        # # thread
        # self.thread = Thread(target=self.run)
        # self.llm = llm
        pass

    def run(self):
        # while self.active:
        #     try:
        #         agent_request = self.agent_process_queue.get(block=True, timeout=1)
        #         self.process(agent_request)
        #     except Empty:
        #         pass
        #     self.count += 1
        pass
    
    def start(self):
        """start the scheduler"""
        self.active = True
        self.thread.start()

    def stop(self):
        """stop the scheduler"""
        self.active = False
        self.thread.join()

    def execute_request(self, agent_process):
        agent_process.set_status("Executing")
        response = self.llm.address_request(agent_process.prompt)
        agent_process.set_response(response)
        agent_process.set_status("Done")


if __name__ == "__main__":
    llm = "llama"
    scheduler = BaseScheduler(llm)
