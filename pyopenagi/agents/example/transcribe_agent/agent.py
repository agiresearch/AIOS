from ...react_agent import ReactAgent
class TranscribeAgent(ReactAgent):
    def __init__(self,
                 agent_name,
                 task_input,
                 agent_process_factory,
                 log_mode: str
        ):
        ReactAgent.__init__(self, agent_name, task_input, agent_process_factory, log_mode)
        self.workflow_mode = "manual"
    def manual_workflow(self):
        workflow = [
                {
                    "message": "figure out what to do with the audio",
                    "tool_use": [ "transcriber/transcriber"],
                    },
                {
                    "message": "organize the information and respond to the user",
                    "tool_use": [ ],
                    },
                ]
        return workflow

    def run(self):
        return super().run()
