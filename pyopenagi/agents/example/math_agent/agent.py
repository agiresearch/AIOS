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
        workflow = [
            {
                "message": "identify the tool to call to do some pre-calculation. ",
                "tool_use": ["wolfram_alpha", "currency_converter"]
            },
            {
                "message":"perform mathematical operations using the pre-calculated result, which could involve addition, subtraction, multiplication, or division with other numeric values to solve the problem.",
                "tool_use": None
            }
        ]
        return workflow

    def run(self):
        return super().run()
