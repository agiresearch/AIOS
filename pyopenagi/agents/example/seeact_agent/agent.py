import time
from pyopenagi.utils.logger import AgentLogger
from seeact.agent import SeeActAgent as SeeActCore
from seeact.demo_utils.inference_engine import Engine
from pyopenagi.utils.chat_template import Query
from aios.hooks.request import send_request

class SeeActAgent:
    def __init__(self, agent_name, task_input, log_mode: str):
        """
        Initialize the SeeAct Agent
        """
        self.agent_name = agent_name
        self.task_input = task_input
        self.log_mode = log_mode
        self.logger = AgentLogger(self.agent_name, self.log_mode)
        self.logger.level_color = {
            "error": "red",
            "warn": "yellow",
            "info": "green",
            "debug": "blue"
        }

        self.seeact = SeeActCore(
            model="gpt-4o",
            default_task=task_input,
            default_website="https://www.google.com/",
            headless=True
        )

        # Replace the generate method
        def custom_generate(self_engine, prompt: list = None, max_new_tokens=4096, temperature=None, 
                          model=None, image_path=None, ouput_0=None, turn_number=0, **kwargs):
            try:
                # Keep the original rate limiting logic
                self_engine.current_key_idx = (self_engine.current_key_idx + 1) % len(self_engine.time_slots)
                start_time = time.time()
                if (
                        self_engine.request_interval > 0
                        and start_time < self_engine.next_avil_time[self_engine.current_key_idx]
                ):
                    wait_time = self_engine.next_avil_time[self_engine.current_key_idx] - start_time
                    print(f"Wait {wait_time} for rate limitting")
                    time.sleep(wait_time)

                prompt0, prompt1, prompt2 = prompt

                if turn_number == 0:
                    prompt_input = [
                        {"role": "system", "content": prompt0},
                        {"role": "user", "content": prompt1}
                    ]
                else:
                    prompt_input = [
                        {"role": "system", "content": prompt0},
                        {"role": "user", "content": prompt1},
                        {"role": "assistant", "content": ouput_0},
                        {"role": "user", "content": prompt2}
                    ]

                # Use correct message format and return value handling
                response, start_times, end_times, waiting_times, turnaround_times = send_request(
                    agent_name=agent_name,
                    query=Query(
                        messages=prompt_input,
                        tools=None,
                        message_return_type="json"
                    )
                )

                # Update rate limiting time
                if self_engine.request_interval > 0:
                    self_engine.next_avil_time[self_engine.current_key_idx] = (
                        max(start_time, self_engine.next_avil_time[self_engine.current_key_idx])
                        + self_engine.request_interval
                    )

                return response.response_message
                
            except Exception as e:
                print(f"Error in generate: {str(e)}")
                raise

        # Replace the engine's generate method
        self.seeact.engine.generate = custom_generate.__get__(self.seeact.engine)
        
        self.start_time = None
        self.end_time = None
        self.created_time = time.time()

    async def run(self):
        try:
            self.start_time = time.time()
            await self.seeact.start()
            
            while not self.seeact.complete_flag:
                try:
                    prediction_dict = await self.seeact.predict()
                    if prediction_dict:
                        await self.seeact.execute(prediction_dict)
                except Exception as e:
                    self.logger.log(f"Error occurred: {e}", "info")
            
            await self.seeact.stop()
            self.end_time = time.time()
            
            return {
                "agent_name": self.agent_name,
                "result": "Task completed",
                "turnaround_time": self.end_time - self.start_time
            }
            
        except Exception as e:
            self.logger.log(f"Error in run method: {str(e)}", "info")
            return {
                "status": "error",
                "error": str(e)
            }

# Register the agent
SeeactAgent = SeeActAgent