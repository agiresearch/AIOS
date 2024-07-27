from pyopenagi.agents.interact import Interactor

def list_agent():
    interactor = Interactor()
    agents = interactor.list_available_agents()
    for agent in agents:
        print(agent)

if __name__ == "__main__":
    list_agent()
