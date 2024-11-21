from cerebrum.manager.agent import AgentManager
from cerebrum.llm.adapter import LLMAdapter
from cerebrum.runtime.process import RunnableAgent

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
    def from_foundational(cls, name: str):
        _llm_factory = LLMAdapter(name)

        _llm = _llm_factory.get_model()

        return _llm


class AutoAgentGenerator:
    
    @classmethod
    def build_agent(cls, agent_name: str, llm_name: str):
        agent, config = AutoAgent.from_pretrained(agent_name)
        llm = AutoLLM.from_foundational(llm_name)

        _agent = RunnableAgent(agent, config, llm)

        print(config)
        
        # _agent.llm = llm

        return _agent