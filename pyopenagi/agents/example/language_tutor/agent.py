from ...react_agent import ReactAgent

class LanguageTutor(ReactAgent):
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
                "message": "Identify user's target language and learning goals.",
                "tool_use": []
            },
            {
                "message": "Generate vocabulary lists and exercises.",
                "tool_use": ["google_search"]
            },
            {
                "message": "Create grammar explanations and practice sentences.",
                "tool_use": []
            },
            {
                "message": "Provide audio examples of pronunciation.",
                "tool_use": ["text_to_speech"]
            },
            {
                "message": "Engage in conversation practice with the user.",
                "tool_use": []
            }
        ]
        return workflow

    def run(self):
        return super().run()
