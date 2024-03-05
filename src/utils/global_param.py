from concurrent.futures import ThreadPoolExecutor

import os

from src.agents.agent_process import (
    AgentProcess,
    AgentProcessQueue
)

global thread_pool
thread_pool = ThreadPoolExecutor(max_workers=64)

global agent_process_queue
agent_process_queue = AgentProcessQueue()

global MAX_AID 
MAX_AID = 256

global aid_pool
aid_pool = [False for i in range(MAX_AID)]

global agent_pool
agent_pool = []

global agent_table
agent_table = {
    "MathAgent": "src.agents.math_agent",
    "NarrativeAgent": "src.agents.narrative_agent"
}