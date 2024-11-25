from cerebrum.manager.agent import AgentManager
from cerebrum.runtime.process import LLMProcessor, RunnableAgent

from .. import config

class AutoAgent:
    MANAGER = AgentManager('https://my.aios.foundation')

    @classmethod
    def from_pretrained(cls, name: str):
        _author, _name = name.split('/')

        _author, _name, _version = cls.MANAGER.download_agent(_author, _name)

        agent, config = cls.MANAGER.load_agent(
            _author,
            _name,
            _version
        )

        return agent, config


class AutoLLM:
    @classmethod
    def from_dynamic(cls):
        return LLMProcessor(config.global_client)


class AutoAgentGenerator:
    
    @classmethod
    def build_agent(cls, agent_name: str, llm_name: str):
        agent, config = AutoAgent.from_pretrained(agent_name)
        llm = AutoLLM.from_foundational(llm_name)

        _agent = RunnableAgent(agent, config, llm)

        print(config)
        
        # _agent.llm = llm

        return _agent