from agent_process import (
    AgentProcess,
    AgentProcessQueue
)

class BaseAgent:
    def __init__(self, config):
        self.config = self.load_config()
        self.name = self.config["name"]
        self.prefix = self.config["description"]

    def run(self):
        '''Execute each step to finish the task.'''
        pass

    def load_config(self):
        config_file = os.path.join(os.getcwd(), "src", "agents", "agent_config/{}.json".format(kernel_type))
        with open(config_file, "r") as f:
            config = json.load(f)
            return config

    def send_request(self, prompt):
        AgentProcessQueue().add(AgentProcess(self.name, self.aid, prompt))

    def get_response(self):
        pass

    def set_aid(self, aid):
        self.aid = aid

    def get_aid(self):
        return self.aid

    def set_status(self, status):
        self.status = status

    def get_status(self):
        return self.status

    def parse_result(self, prompt):
        pass
        