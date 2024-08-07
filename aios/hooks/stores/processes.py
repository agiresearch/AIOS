from concurrent.futures import Future

AGENT_PROCESSES: list[Future] = []

def addProcess(p: Future) -> None:
    AGENT_PROCESSES.append(p)

def clearProcesses() -> None:
    AGENT_PROCESSES.clear()
