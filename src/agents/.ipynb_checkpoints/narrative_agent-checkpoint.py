class NovelAgent(BaseAgent):
    def __init__(self, config):
        super(BaseAgent, self).__init__(config)
    
    def send_request(self, instruction):
        pass

    def get_response(self):
        pass
    
    def run(self, task_input):
        prompt = ""
        prefix = self.prefix
        prompt += prefix
        
        task_input = "Given the task: " + task_input
        prompt += task_input
        
        steps = [
            "Develop the story's setting and characters, establish a background and introduce the main characters.",
            "Given the background and characters, create situations that lead to the rising action, develop the climax with a significant turning point, and then move towards the resolution.",
            "Conclude the story and reflect on the narrative. This could involve tying up loose ends, resolving any conflicts, and providing a satisfactory conclusion for the characters."
        ]

        for i, step in enumerate(steps):
            prompt += "In step {}: ".format(i) + step
            self.send_request(prompt)
            response = self.get_response()
            prompt += "Generated content at step {} is: ".format(i) + response

        res = self.parse_result(prompt)
        return res

    def parse_result(self, prompt):
        return prompt