import os

class BaseContextManager:
    def __init__(self):
        self.context_dir = os.path.join(os.getcwd(), "src", "context", "context_restoration")
        if not os.path.exists(self.context_dir):
            os.makedirs(self.context_dir)

    def start(self):
        pass

    def gen_snapshot(self, pid, context):
        pass

    def gen_recover(self, pid):
        pass

    def stop(self):
        pass
