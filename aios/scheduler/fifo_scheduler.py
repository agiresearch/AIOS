# This implements a (mostly) FIFO task queue using threads and queue, in a
# similar fashion to the round robin scheduler. However, the timeout is 1 second
# instead of 0.05 seconds.

from .base import BaseScheduler
from aios.hooks.types.llm import QueueGetMessage

from queue import Queue, Empty

import traceback
import time

class FIFOScheduler(BaseScheduler):
    def __init__(self, llm, log_mode, get_queue_message: QueueGetMessage):
        super().__init__(llm, log_mode)
        self.agent_process_queue = Queue()
        self.get_queue_message = get_queue_message

    def run(self):
        while self.active:
            try:
                # wait at a fixed time interval, if there is nothing received in the time interval, it will raise Empty
                agent_request = self.get_queue_message()

                agent_request.set_status("executing")
                self.logger.log(
                    f"{agent_request.agent_name} is executing. \n", "execute"
                )
                agent_request.set_start_time(time.time())
                
                self.execute_request(agent_request)

                self.logger.log(
                    f"Current request of {agent_request.agent_name} is done. Thread ID is {agent_request.get_pid()}\n", "done"
                )
                # wait at a fixed time interval, if there is nothing received in the time interval, it will raise Empty
                agent_request = self.get_queue_message()

                agent_request.set_status("executing")
                self.logger.log(
                    f"{agent_request.agent_name} is executing. \n", "execute"
                )
                agent_request.set_start_time(time.time())
                
                self.execute_request(agent_request)

                self.logger.log(
                    f"Current request of {agent_request.agent_name} is done. Thread ID is {agent_request.get_pid()}\n", "done"
                )

            except Empty:
                pass


            except Exception:
                traceback.print_exc()

    def execute_request(self, agent_request):
        action_type = agent_request.query.action_type

        if action_type in ["message_llm", "call_tool"]:
            response = self.llm.address_request(agent_request)
            # print(response)
            agent_request.set_response(response)
            
            # self.llm.address_request(agent_request)

        # elif action_type == "operate_file":
        #     api_calls = self.lsfs_parser.parse(agent_request)
        #     response = self.lsfs.execute_calls(api_calls)
        #     agent_request.set_response(response)
        agent_request.event.set()
        agent_request.set_status("done")
        agent_request.set_end_time(time.time())
