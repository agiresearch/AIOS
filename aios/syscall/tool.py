from aios.syscall.syscall import Syscall

class ToolSyscall(Syscall):
    def __init__(self, agent_name, request):
        super().__init__(agent_name, request)
        self.tool_calls = request
