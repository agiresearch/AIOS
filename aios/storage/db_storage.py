# TODO: Not implemented
# Storing to databases has not been implemented yet

from aios.storage.base import BaseStorage


class DBStorage(BaseStorage):
    def __init__(self):
        pass

    def sto_save(self, agent_id, content):
        pass

    def sto_load(self, agent_id):
        pass

    def sto_alloc(self, agent_id):
        pass

    def sto_clear(self, agent_id):
        pass
