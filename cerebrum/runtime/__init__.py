
# from cerebrum.agents.base import BaseAgent
# from cerebrum.llm.base import BaseLLM


from cerebrum.runtime.process import RunnableAgent


class Pipeline:
    def __init__(self):
        self.agent_classes = dict()
        self.llms = dict()
        self.running_processes = []
        self.responses = []


    def add_agent(self, agent_class, config, order: int):
        self.agent_classes[order] = {
            'agent_class': agent_class,
            'config': config
        }
        
        return self

    def add_llm(self, llm, order: int):
        self.llms[order] = llm
        return self

    
    def run(self, query: str):
        agent_keys, llm_keys = list(self.agent_classes.keys()), list(self.llms.keys())

        if len(agent_keys) != len (llm_keys):
            return False
        
        agent_keys.sort()

        for k in agent_keys:
            # support single step pipelines for now
            if k != agent_keys[-1]:
                return False
            else:
                _agent = RunnableAgent(
                    self.agent_classes.get(k).get('agent_class'),
                    self.agent_classes.get(k).get('config'), 
                    self.llms.get(k)
                )

                self.running_processes.append(_agent)

        for process in self.running_processes:
            res = _agent.run(query)
            self.responses.append(res)

        return self.responses[0]
