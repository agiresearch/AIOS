from ...react_agent import ReactAgent
class CreationAgent(ReactAgent):
    def __init__(self,
                 agent_name,
                 task_input,
                 agent_process_factory,
                 log_mode: str
        ):
        ReactAgent.__init__(self, agent_name, task_input, agent_process_factory, log_mode)
        self.workflow_mode = "automatic"

    def automatic_workflow(self):
        return super().automatic_workflow()

    def manual_workflow(self):
        workflow = [
            {
                "message": "filled in more details about the user's requirement",
                "tool_use": None
            },
            {
                "message": "generate an image based on the user's requirements and filled details",
                "tool_use": ["sdxl-turbo"]
            }
        ]
        return workflow

    def run(self):
        return super().run()
