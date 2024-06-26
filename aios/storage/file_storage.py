# Storing to json files to offload conversation history

from aios.storage.base import BaseStorage

import json

class JsonStorage(BaseStorage):
    def __init__(self):
        pass

    def sto_save(self, agent_id, content):
        with open("aios/storage/agent" + str(agent_id) + ".json", "w") as f:
            json.dump(content, f, indent=2)

    def sto_load(self, agent_id):
        with open("aios/storage/agent" + str(agent_id) + ".json", "r") as f:
            interaction_history = json.load(f)
            return interaction_history

    def sto_alloc(self, agent_id):
        return NotImplementedError

    def sto_clear(self, agent_id):
        return NotImplementedError
