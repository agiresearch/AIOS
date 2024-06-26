# This manages restoring and snapshotting the context.
# The file is used in the BaseLLM class and the RRScheduler class.

from aios.context.base import BaseContextManager

import os

import torch

# import shutil

class SimpleContextManager(BaseContextManager):
    def __init__(self):
        BaseContextManager.__init__(self)

    def start(self):
        pass

    def gen_snapshot(self, pid, context):
        file_path = os.path.join(self.context_dir, f"process-{pid}.pt")
        torch.save(context, file_path)

    def gen_recover(self, pid):
        file_path = os.path.join(self.context_dir, f"process-{pid}.pt")
        return torch.load(file_path)

    def check_restoration(self, pid):
        return os.path.exists(os.path.join(self.context_dir, f"process-{pid}.pt"))

    def clear_restoration(self, pid):
        # print(f"Process {pid} has been deleted.")
        os.remove(os.path.join(self.context_dir, f"process-{pid}.pt"))

    def stop(self):
        pass
