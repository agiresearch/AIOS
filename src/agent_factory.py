from src.agents.math_agent import MathAgent

from src.agents.narrative_agent import NarrativeAgent

import time

from datetime import datetime

from src.memory.single_memory import SingleMemory

import sys

from src.utils.global_param import (
    MAX_AID,
    aid_pool,
    agent_pool,
    agent_table
)

class AgentFactory:
    def __init__(self):
        # self.MAX_AID = 256

        # self.aid_pool = [False for i in range(self.MAX_AID)]
        
        # self.agent_pool = []
        
        # self.agent_list = {
        #     "MathAgent": MathAgent,
        #     "NarrativeAgent": NarrativeAgent
        # }
        pass
        
    # def activate_agent(self, agent_name, task_input):
    #     agent = self.agent_list[agent_name](agent_name, task_input)
    #     aid = -1
    #     for id, used in enumerate(self.aid_pool):
    #         if used is False:
    #             aid = id
    #             self.aid_pool[id] = True
    #             break
                
    #     agent.set_aid(aid)
    #     time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    #     agent.memory_pool = SingleMemory()
        
    #     agent.set_status("Active")
    #     agent.set_created_time(time)
        
    #     self.agent_pool.append(agent)
    #     return agent
    
    
    def deactivate_agent(self, agent):
        # idx = -1
        while agent.get_status() != "Inactive":
            if agent.get_status() == "Done":
                time.sleep(5)
                agent.set_status("Inactive")
                self.aid_pool[agent.get_aid()] = False
                # idx = i
                # break
    
        time.sleep(10)
        idx = -1
        for i, a in enumerate(self.agent_pool):
            if a.get_aid() == agent.get_aid():
                idx = i
                break
        if idx != -1:
            del self.agent_pool[agent.get_aid()]

    def print(self):
        # while True:
        #     print_str = ""
        for agent in agent_pool:
            print(f"| Agent ID: {agent.get_aid()} | Agent Name: {agent.agent_name} | Status: {agent.get_status()} | Activated Time: {agent.get_created_time()} |")
        # print("\n")
        # sys.stdout.write(print_str)
        # sys.stdout.flush()
        
        time.sleep(2)
            
