from ...react_agent import ReactAgent

class FashionStylist(ReactAgent):
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
                "message": "Gather user preferences, body type, and occasion details.",
                "tool_use": []
            },
            {
                "message": "Generate outfit ideas based on user input.",
                "tool_use": []
            },
            {
                "message": "Create visual representations of outfit ideas.",
                "tool_use": ["text_to_image"]
            },
            {
                "message": "Analyze generated images for style coherence and alignment with user preferences.",
                "tool_use": ["doc_question_answering"]
            },
            {
                "message": "Search for similar items online based on the generated outfit ideas.",
                "tool_use": ["google_search"]
            },
            {
                "message": "Provide outfit recommendations and links to purchase similar items.",
                "tool_use": []
            }
        ]
        return workflow

    def run(self):
        return super().run()
