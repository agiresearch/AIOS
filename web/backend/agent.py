import json

class BaseAgent:
    def __init__(self, config: str):
        with open(config, 'r') as file:
            data: dict[str, dict] = json.load(file)

        self.name = data.get('meta').get('name')
        self.author = data.get('meta').get('author')
        self.version = data.get('meta').get('version')
        self.description = data.get('meta').get('description')

    def run():
        pass


class NewAgent(BaseAgent):
    def __init__(self, config: str, *args, **kwargs):
        super().__init__(self, config)

        #own stuff here

    def run(self):
        pass
        # own stuff here