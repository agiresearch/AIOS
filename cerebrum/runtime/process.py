from typing import Any, Type

# from cerebrum.agents.base import BaseAgent
# from cerebrum.llm.base import BaseLLM
from cerebrum.client import Cerebrum
from cerebrum.llm.communication import LLMQuery
from cerebrum.utils.chat import Query

class LLMProcessor:
    def __init__(self, client: Cerebrum):
        self.client = client

    def process(self, agent_name: str, query: LLMQuery):
        return self.client._query_llm(agent_name=agent_name, query=query)

class RunnableAgent:
    def __init__(self, client: Cerebrum, name: str):
        self.name = name
        self.client = client

    def execute(self, query: str):
        result = self.client.execute(self.name, {
            "task": self.query,
        })

        # Wait for completion
        try:
            final_result = self.client.poll_agent(
                result["execution_id"],
                timeout=300  # 5 minutes timeout
            )
            return final_result
        except TimeoutError:
            return "Agent execution timed out"


class AgentProcessor:
    @staticmethod
    def process_response(query: Query, llm: Any):
        print(query)
        print(llm)
        return llm.execute(query)

    @staticmethod
    def make_runnable(agent_class: Type[Any], query: str, config: dict):
        _agent = agent_class(
            'test',
            query,
            config
        )

        return _agent

