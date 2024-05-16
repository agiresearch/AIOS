from src.llm_kernel.llms import LLMKernel
from openagi.src.agents.agent_process import AgentProcess
from src.utils.message import Message as AGIMessage

from src.memory.os.handler import MemoryHandler


def test_infinite_memory():
    def build_query(phrase: str):
        llm_type = "gemini-pro"
        llm = LLMKernel(llm_type, max_new_tokens = 400)
        agent_process = AgentProcess(
            agent_name="Narrative Agent",
            message = AGIMessage(
                prompt=phrase
            )
        )

        llm.address_request(agent_process)
        
        return agent_process.get_response().response_message

    handler = MemoryHandler(execute=build_query)
    
    response = handler.chain('Tell me a story about a fish, it should be able to continued infinitely.')

    for x in range(0,5):
        response = handler.chain('What happened next? Remember to spin it out for infinity!')
        assert isinstance(response, str), "The response should be a string"