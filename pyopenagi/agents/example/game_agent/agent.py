from ...react_agent import ReactAgent

class GameAgent(ReactAgent):
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
                "message": "Gather user preferences (genre, platform, play style)",
                "tool_use": []
            },
            {
                "message": "Search for suitable games based on criteria",
                "tool_use": ["google_search"]
            },
            {
                "message": "Provide game descriptions, ratings, and gameplay details",
                "tool_use": []
            }
        ]
        return workflow

    def run(self):
        return super().run()
