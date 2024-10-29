import importlib
import os
import time
from aios.hooks.request import send_request
from pyopenagi.utils.chat_template import Query
from pyopenagi.utils.logger import AgentLogger
from seeact.agent import SeeActAgent as SeeActCore

class SeeActAgent:
    def __init__(self, agent_name, task_input, log_mode: str):
        self.agent_name = agent_name
        self.task_input = task_input
        self.log_mode = log_mode
        self.logger = AgentLogger(self.agent_name, self.log_mode)
        
        # seeact core instance
        self.seeact = SeeActCore(
            model="gpt-4o",  # Use AIOS model
            default_task=task_input,
            default_website="https://www.google.com/",
            headless=True
        )
        
        # For statistics
        self.start_time = None
        self.end_time = None
        self.created_time = time.time()
        self.request_waiting_times = []
        self.request_turnaround_times = []
        
    async def run(self):
        try:
            self.start_time = time.time()
            
            # Start seeact
            await self.seeact.start()
            
            # Execute task until completion
            while not self.seeact.complete_flag:
                try:
                    prediction_dict = await self.seeact.predict()
                    if prediction_dict:
                        await self.seeact.execute(prediction_dict)
                except Exception as e:
                    self.logger.log(f"Error: {e}", "error")
                    
            await self.seeact.stop()
            
            self.end_time = time.time()
            
            return {
                "agent_name": self.agent_name,
                "result": "Task completed",
                "turnaround_time": self.end_time - self.start_time
            }
            
        except Exception as e:
            self.logger.log(f"Error in run method: {str(e)}", "error")
            return {
                "status": "error",
                "error": str(e)
            }
SeeactAgent = SeeActAgent
