from .base import BaseScheduler

from queue import Queue, Empty
from threading import Thread

import time
class FIFOScheduler(BaseScheduler):
    def __init__(self, llm, agent_process_queue, llm_request_responses, log_mode):
        BaseScheduler.__init__(self, llm, agent_process_queue, llm_request_responses, log_mode)

    def run(self):
        while True:
            # time.sleep(1)
            if not self.agent_process_queue.empty():
                # print("active")
                llm_request = self.agent_process_queue.get()

                llm_request.set_start_time(time.time())

                llm_request.set_status("executing")

                self.logger.log(
                    f"{llm_request.agent_name}[ID={llm_request.agent_id}] is switched to executing.\n",
                    level = "execute"
                )
                response = self.execute_request(llm_request)

                llm_request.set_end_time(time.time())

                task_key = (llm_request.agent_id, llm_request.step)

                if task_key in self.llm_request_responses:
                    self.llm_request_responses[task_key]["response"] = response
                    self.llm_request_responses[task_key]["status"] = llm_request.get_status()
                    self.llm_request_responses[task_key]["created_times"].append(llm_request.get_created_time())
                    self.llm_request_responses[task_key]["start_times"].append(llm_request.get_start_time())
                    self.llm_request_responses[task_key]["end_times"].append(llm_request.get_end_time())

                else:
                    self.llm_request_responses[task_key] = {
                        "response": response,
                        "status": llm_request.get_status(),
                        "created_times": [llm_request.get_created_time()],
                        "start_times": [llm_request.get_start_time()],
                        "end_times": [llm_request.get_end_time()]
                    }

    def execute_request(self, llm_request):
        result = self.llm.address_request(
            llm_request=llm_request
        )
        return result
