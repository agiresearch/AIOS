from agent import (
    MathAgent,
    NovelAgent
)

MAX_AID = 256

AID_POOL = [False for i in range(MAX_UID)]

AGENT_POOL = []

agent_list = {
    "MathAgent": MathAgent,
    "NovelAgent": NovelAgent
}

def create_agent(agent_name):
    agent = agent_list[agent_name]()
    aid = -1
    for id, used in enumerate(MAX_AID):
        if used is False:
            aid = id
            MAX_AID[id] = True
            break
    agent.set_aid(aid)
    AGENT_POOL.append(agent)
    return agent


def destroy_agent():
    pass
                