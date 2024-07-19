
from ...react_agent import ReactAgent

class RecAgent(ReactAgent):
    def __init__(self,
                 agent_name,
                 task_input,
                 agent_process_factory,
                 log_mode
        ):
        ReactAgent.__init__(self, agent_name, task_input, agent_process_factory, log_mode)

    def automatic_workflow(self):
        return super().automatic_workflow()

    def manual_workflow(self):
        workflow = [
            {
                "message": "identify the tool that you need to call to obtain information.",
                "tool_use": ["imdb/top_movies", "imdb/top_series"]
            },
            {
                "message": "based on the information, give recommendations for the user based on the constrains. ",
                "tool_use": None
            }
        ]
        return workflow

    def run(self):
        return super().run()
