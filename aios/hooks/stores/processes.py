from concurrent.futures import Future

AGENT_PROCESSES: dict[str, Future] = {}

AGENT_IDS: list[int]

def addProcess(p: Future, pi: str) -> None:
    # AGENT_PROCESSES.append(p)
    AGENT_PROCESSES[pi] = p

def clearProcesses() -> None:
    AGENT_PROCESSES.clear()

