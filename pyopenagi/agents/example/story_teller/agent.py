from ...react_agent import ReactAgent

import os
class StoryTeller(ReactAgent):
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
                "message": "Determine the story genre and theme based on user input.",
                "tool_use": []
            },
            {
                "message": "Generate initial story plot and characters.",
                "tool_use": []
            },
            {
                "message": "Create visual representations for the main character.",
                "tool_use": ["text_to_image"]
            },
            {
                "message": "Write descriptive text for each image and analyze each image",
                "tool_use": ["doc_question_answering"]
            },
            {
                "message": "Incorporate it into the story narrative.",
                "tool_use": []
            }
        ]
        return workflow

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

    def run(self):
        return super().run()
