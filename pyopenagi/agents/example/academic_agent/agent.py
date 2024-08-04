from ...react_agent import ReactAgent

class AcademicAgent(ReactAgent):
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
                "message": "Gather research topic and keywords",
                "tool_use": []
            },
            {
                "message": "Search for relevant papers on arXiv and Wikipedia",
                "tool_use": ["arxiv", "wikipedia"]
            },
            {
                "message": "Summarize key findings of selected papers",
                "tool_use": []
            },
            {
                "message": "Identify research gaps and generate potential research questions",
                "tool_use": []
            }
        ]
        return workflow

    def run(self):
        return super().run()
