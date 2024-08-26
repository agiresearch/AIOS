from ...react_agent import ReactAgent

class TechSupportAgent(ReactAgent):
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
                "message": "identify the user's technical issue or requirement",
                "tool_use": []
            },
            {
                "message": "search for troubleshooting steps for the identified issue",
                "tool_use": ["google_search"]
            },
            {
                "message": "organize the above information and summarize the solution",
                "tool_use": []
            }
        ]
        return workflow

    def run(self):
        return super().run()
