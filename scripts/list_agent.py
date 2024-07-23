import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pyopenagi.agents.interact import Interactor

def list_agent():
    interactor = Interactor()
    agents = interactor.list_available_agents()
    for agent in agents:
        print(agent)

if __name__ == "__main__":
    list_agent()
