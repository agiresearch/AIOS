from ...react_agent import ReactAgent
class TranscribeAgent(ReactAgent):
    def __init__(self,
                 agent_name,
                 task_input,
                 agent_process_factory,
                 log_mode: str
        ):
        ReactAgent.__init__(self, agent_name, task_input, agent_process_factory, log_mode)
        self.workflow_mode = "automatic"
    def manual_workflow(self):
        pass
    def run(self):
        return super().run()