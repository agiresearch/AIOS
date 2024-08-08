from ...react_agent import ReactAgent
import os
class LogoCreator(ReactAgent):
    def __init__(self,
                 agent_name,
                 task_input,
                 agent_process_factory,
                 log_mode: str
        ):
        ReactAgent.__init__(self, agent_name, task_input, agent_process_factory, log_mode)
        self.workflow_mode = "manual"

    def check_path(self, tool_calls):
        script_path = os.path.abspath(__file__)
        save_dir = os.path.join(os.path.dirname(script_path), "output") # modify the customized output path for saving outputs
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)
        for tool_call in tool_calls:
            try:
                for k in tool_call["parameters"]:
                    if "path" in k:
                        path = tool_call["parameters"][k]
                        if not path.startswith(save_dir):
                            tool_call["parameters"][k] = os.path.join(save_dir, os.path.basename(path))
            except Exception:
                continue
        return tool_calls

    def automatic_workflow(self):
        return super().automatic_workflow()

    def manual_workflow(self):
        workflow = [
            {
                "message": "Gather business information (name, industry, target audience)",
                "tool_use": []
            },
            {
                "message": "Identify brand personality and values",
                "tool_use": []
            },
            {
                "message": "Generate logo concepts and variations",
                "tool_use": ["text_to_image"]
            }
        ]
        return workflow

    def run(self):
        return super().run()
