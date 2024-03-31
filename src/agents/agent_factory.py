from datetime import datetime

import heapq

from src.utils.global_param import (
    MAX_AID,
    agent_pool,
    agent_table
)
class AgentFactory:
    def __init__(self, llm, agent_process_queue):
        self.MAX_AID = MAX_AID
        self.llm = llm
        self.aid_pool = [i for i in range(self.MAX_AID)]
        heapq.heapify(self.aid_pool)
        self.agent_process_queue = agent_process_queue
        
        self.agent_table = agent_table
        self.agent_pool = agent_pool
        
    def activate_agent(self, agent_name, task_input):
        agent = self.agent_table[agent_name](
            agent_name = agent_name, 
            task_input = task_input,
            llm = self.llm,
            agent_process_queue = self.agent_process_queue
        )
        aid = heapq.heappop(self.aid_pool)
        
        agent.set_aid(aid)
        time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        agent.set_status("Active")
        agent.set_created_time(time)
        
        self.agent_pool[aid] = agent
        return agent
    
    def deactivate_agent(self, aid):
        self.agent_pool.popitem(aid)
        heapq.heappush(self.aid_pool, aid)
        # self.aid_pool.heappush(aid)

    def print(self):
        for aid, agent in agent_pool:
            print(f"| Agent ID: {aid} | Agent Name: {agent.agent_name} | Status: {agent.get_status()} | Activated Time: {agent.get_created_time()} |")
            
