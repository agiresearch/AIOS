from ...react_agent import ReactAgent

class LogoCreator(ReactAgent):
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
                "message": "Gather business information (name, industry, target audience)",
                "tool_use": []
            },
            {
                "message": "Identify brand personality and values",
                "tool_use": []
            },
            {
                "message": "Generate logo concepts and variations",
                "tool_use": ["text_to_image"]
            }
        ]
        return workflow

    def run(self):
        return super().run()
