from base import BaseStorage

import json

class JsonStorage(BaseStorage):
    def __init__(self):
        pass

    def save(self, interaction_history, path):
        with open(path, "w") as f:
            json.dump(interaction_history, f, indent=2)

    def load(self, path):
        with open(path, "r") as f:
            interaction_history = json.load(f)
            return interaction_history


class TxtStorage(BaseStorage):
    def __init__(self):
        pass

    def save(self, interaction_history, path):
        pass
        
    def load(self, path):
        pass