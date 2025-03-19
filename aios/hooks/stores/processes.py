from concurrent.futures import Future

AGENT_PROCESSES: dict[str, Future] = {}

AGENT_IDS: list[int]

def addProcess(p: Future, pi: str) -> None:
    # AGENT_PROCESSES.append(p)
    AGENT_PROCESSES[pi] = p

def clearProcesses() -> None:
    AGENT_PROCESSES.clear()

def getProcessStatus(process_id: str) -> dict:
    """
    Get the status of a process without blocking.
    
    Args:
        process_id (str): The ID of the process to check.
        
    Returns:
        dict: A dictionary containing the process status.
        
    Raises:
        ValueError: If the process ID is not found.
    """
    future = AGENT_PROCESSES.get(process_id)
    
    if not future:
        raise ValueError(f"Process with ID '{process_id}' not found")
        
    status = {
        "id": process_id,
        "running": not future.done(),
        "cancelled": future.cancelled(),
        "done": future.done(),
        "exception": future.exception() if future.done() and not future.cancelled() else None,
    }
    
    return status

