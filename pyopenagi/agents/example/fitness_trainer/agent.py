from ...react_agent import ReactAgent

class FitnessTrainer(ReactAgent):
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
                "message": "Gather information about the user's fitness level, goals, and any physical limitations.",
                "tool_use": []
            },
            {
                "message": "Create a detailed workout plan with exercise descriptions.",
                "tool_use": []
            },
            {
                "message": "Generate images demonstrating key exercises in the workout plan.",
                "tool_use": ["text_to_image"]
            },
            {
                "message": "Create audio instructions for each exercise to guide the user.",
                "tool_use": ["text_to_speech"]
            },
            {
                "message": "Compile the workout plan, images, and audio into a comprehensive fitness guide.",
                "tool_use": []
            }
        ]
        return workflow

    def run(self):
        return super().run()
