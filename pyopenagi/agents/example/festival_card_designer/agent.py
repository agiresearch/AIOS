from ...react_agent import ReactAgent

class FestivalCardDesigner(ReactAgent):
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
                "message": "Gather user information (festival theme, target audience, card size)",
                "tool_use": []
            },
            {
                "message": "Identify card design elements (colors, fonts, imagery)",
                "tool_use": []
            },
            {
                "message": "Generate card layout options",
                "tool_use": ["text_to_image"]
            },
            {
                "message": "Add textual elements to the festival card ",
                "tool_use": []
            }
        ]
        return workflow

    def run(self):
        return super().run()
