from ...react_agent import ReactAgent

class PlantCareAssistant(ReactAgent):
    def __init__(self,
                 agent_name,
                 task_input,
                 agent_process_factory,
                 log_mode: str
        ):
        ReactAgent.__init__(self, agent_name, task_input, agent_process_factory, log_mode)
        self.workflow_mode = "manual"

    def automatic_workflow(self):
        return super().automatic_workflow()

    def manual_workflow(self):
        workflow = [
            {
                "message": "Gather plant information (type, age, environment)",
                "tool_use": []
            },
            {
                "message": "Identify plant needs (light, water, fertilizer)",
                "tool_use": ["wikipedia"]
            },
            {
                "message": "Create a plant care schedule",
                "tool_use": []
            },
            {
                "message": "Provide troubleshooting advice for plant issues",
                "tool_use": []
            }
        ]
        return workflow

    def run(self):
        return super().run()
