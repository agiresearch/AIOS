from src.agents.math_agent.math_agent import MathAgent

from src.agents.narrative_agent.narrative_agent import NarrativeAgent

from src.agents.rec_agent.rec_agent import RecAgent

global MAX_AID 
MAX_AID = 256

global aid_pool
aid_pool = [False for i in range(MAX_AID)]

global agent_pool
agent_pool = {}

global agent_execution_path
agent_execution_path = {
    "MathAgent": "src.agents.math_agent",
    "NarrativeAgent": "src.agents.narrative_agent",
    "RecAgent": "src.agents.rec_agent",
    "TravelAgent": "src.agents.travel_agent"
}

global agent_table
agent_table = {
    "MathAgent": MathAgent,
    "NarrativeAgent": NarrativeAgent,
    "RecAgent": RecAgent
}