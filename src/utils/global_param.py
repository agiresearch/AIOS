import os

global MAX_AID 
MAX_AID = 256

global aid_pool
aid_pool = [False for i in range(MAX_AID)]

global agent_pool
agent_pool = []

global agent_table
agent_table = {
    "MathAgent": "src.agents.math_agent",
    "NarrativeAgent": "src.agents.narrative_agent",
    "RecAgent": "src.agents.rec_agent"
}