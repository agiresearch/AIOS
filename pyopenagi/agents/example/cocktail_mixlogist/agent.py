from ...react_agent import ReactAgent

class CocktailMixlogist(ReactAgent):
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
                "message": "Gather user preferences (alcoholic or non-alcoholic, taste profile, occasion)",
                "tool_use": []
            },
            {
                "message": "Identify available ingredients and potential substitutions",
                "tool_use": []
            },
            {
                "message": "Create cocktail or mocktail recipes",
                "tool_use": []
            }
        ]
        return workflow

    def run(self):
        return super().run()
