from ...react_agent import ReactAgent

class InteriorDecorator(ReactAgent):
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
                "message": "Gather user preferences, room dimensions, and desired style.",
                "tool_use": []
            },
            {
                "message": "Generate mood board images based on user input using text_to_image.",
                "tool_use": ["text_to_image"]
            },
            {
                "message": "Analyze generated images for color schemes, furniture styles, and overall ambiance.",
                "tool_use": []
            },
            {
                "message": "Recommend specific furniture, decor items, and color palettes based on analysis.",
                "tool_use": []
            }
        ]

        return workflow

    def run(self):
        return super().run()
