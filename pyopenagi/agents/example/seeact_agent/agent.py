import time
from pyopenagi.utils.logger import AgentLogger
from seeact.agent import SeeActAgent as SeeActCore

class SeeActAgent:
    def __init__(self, agent_name, task_input, log_mode: str):
        """
        Initialize the SeeAct Agent
        Args:
            agent_name: Name of the agent
            task_input: Input task to be performed
            log_mode: Logging mode configuration
        """
        self.agent_name = agent_name
        self.task_input = task_input
        self.log_mode = log_mode
        self.logger = AgentLogger(self.agent_name, self.log_mode)
        
        # Add necessary log color configuration
        self.logger.level_color = {
            "error": "red",
            "warn": "yellow", 
            "info": "green",
            "debug": "blue"
        }
        
        # Initialize SeeAct core instance
        self.seeact = SeeActCore(
            model="gpt-4o",  # Use AIOS model
            default_task=task_input,
            default_website="https://www.google.com/",
            headless=True
        )
        
        # For tracking execution time and statistics
        self.start_time = None
        self.end_time = None
        self.created_time = time.time()

    async def run(self):
        """
        Execute the main agent loop
        Returns:
            dict: Contains execution results including agent name, status, and execution time
        """
        try:
            self.start_time = time.time()
            await self.seeact.start()
            
            # Main execution loop
            while not self.seeact.complete_flag:
                try:
                    prediction_dict = await self.seeact.predict()
                    if prediction_dict:
                        await self.seeact.execute(prediction_dict)
                except Exception as e:
                    # Use info level instead of error to avoid color issues
                    self.logger.log(f"Error occurred: {e}", "info")
            
            await self.seeact.stop()
            self.end_time = time.time()
            
            return {
                "agent_name": self.agent_name,
                "result": "Task completed",
                "turnaround_time": self.end_time - self.start_time
            }
            
        except Exception as e:
            # Use info level instead of error to avoid color issues
            self.logger.log(f"Error in run method: {str(e)}", "info")
            return {
                "status": "error",
                "error": str(e)
            }

# Register the agent
SeeActAgent = SeeActAgent