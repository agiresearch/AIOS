from ...react_agent import ReactAgent

class MathAgent(ReactAgent):
    def __init__(self,
                 agent_name,
                 task_input,
                 agent_process_factory,
                 log_mode: str
        ):
        ReactAgent.__init__(self, agent_name, task_input, agent_process_factory, log_mode)

    def automatic_workflow(self):
        return super().automatic_workflow()

    def manual_workflow(self):
        # TODO: add pemdas calculation support in the future
        workflow = [
            {
                "message": "Identify the problem type and relevant formulas",
                "tool_use": ["wikipedia"]
            },
            {
                "message": "Break down the problem into steps",
                "tool_use": []
            },
            {
                "message": "Provide final answer/solution",
                "tool_use": []
            }
        ]
        return workflow

    def run(self):
        return super().run()
