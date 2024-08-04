from ...react_agent import ReactAgent

class CookTherapist(ReactAgent):
    def __init__(self,
                 agent_name,
                 task_input,
                 agent_process_factory,
                 log_mode: str
        ):
        ReactAgent.__init__(self, agent_name, task_input, agent_process_factory, log_mode)
        # self.workflow_mode = "automatic"
        self.workflow_mode = "manual"

    def manual_workflow(self):
        workflow = [
            {
                "message": "Gather user input on desired ingredients, dietary restrictions, or cuisine type.",
                "tool_use": []
            },
            {
                "message": "Create a detailed recipe, including ingredients, measurements, and step-by-step instructions.",
                "tool_use": []
            },
            {
                "message": "Generate an image of the final dish.",
                "tool_use": ["text_to_image"]
            },
            {
                "message": "Present the recipe, including image, instructions, and nutritional information.",
                "tool_use": []
            }
        ]
        return workflow

    def run(self):
        return super().run()
