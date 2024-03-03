from base import math_agent

class MathAgent(BaseAgent):
    def __init__(self, config):
        super(BaseAgent, self).__init__(config)
        

    def send_message(self, instruction):
        pass

    def receive_message(self):
        pass
    
    def run(self, task_input):
        prompt = ""
        prefix = self.prefix
        prompt += prefix
        
        task_input = "Given the task: " + task_input
        prompt += task_input
        
        steps = [
            "Identify and outline the sub-problems that need to be solved as stepping stones toward the solution.",
            "Apply mathematical theorems, formulas to solve each sub-problem.",
            "Integrate the solutions to these sub-problems in the previous step to get the final solution."
        ]

        for i, step in enumerate(steps):
            prompt += "In step {}: ".format(i) + step
            self.send_request(prompt)
            response = self.get_response()
            prompt += "Response at step {} is: ".format(i) + response

        res = self.parse_result(prompt)
        return res

    def parse_result(self, prompt):
        length = prompt.index("Response at step {} is: ")
        final_solution = prompt[length:]
        return final_solution