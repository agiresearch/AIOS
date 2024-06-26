# Stub implementation of storing interactions to the disk

class BaseStorage:
    def __init__(self):
        self.storage_pool = {}

    def sto_save(self, agent_id, content):
        pass

    def sto_load(self, agent_id):
        pass

    def sto_alloc(self, agent_id):
        pass

    def sto_clear(self, agent_id):
        pass
