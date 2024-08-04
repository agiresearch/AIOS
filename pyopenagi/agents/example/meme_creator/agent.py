from ...react_agent import ReactAgent

class MemeCreator(ReactAgent):
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
                "message": "Gather user input (topic, text, image)",
                "tool_use": []
            },
            {
                "message": "Select a suitable meme template or create a custom image",
                "tool_use": ["text_to_image"]
            },
            {
                "message": "Add text to the image based on user input",
                "tool_use": []
            }
        ]
        return workflow

    def run(self):
        return super().run()
