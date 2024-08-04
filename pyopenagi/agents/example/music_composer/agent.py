from ...react_agent import ReactAgent

class MusicComposer(ReactAgent):
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
                "message": "Gather user information about desired music genre, mood, and tempo.",
                "tool_use": []
            },
            {
                "message": "Generate basic melody, chord progression, or rhythm structure.",
                "tool_use": []
            },
            {
                "message": "Provide suggestions for musical development and experimentation.",
                "tool_use": []
            },
            {
                "message": "Convert musical elements into audio.",
                "tool_use": ["text_to_speech"]
            },
            {
                "message": "Offer feedback on composition and suggest improvements.",
                "tool_use": []
            }
        ]
        return workflow

    def run(self):
        return super().run()
