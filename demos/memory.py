# bottom two lines fix src import error 
# replace path with your path to AIOS

# import sys, os
# sys.path.append('C:\\Users\\rkfam\\AIOS')

from src.llm_kernel.llms import LLMKernel
from openagi.src.agents.agent_process import AgentProcess
from src.utils.message import Message as AGIMessage

from src.memory.os.handler import MemoryHandler

import warnings

def fxn():
    warnings.warn("deprecated", DeprecationWarning)

with warnings.catch_warnings():
    warnings.simplefilter("ignore")
    fxn()

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

#10,000's just a really long number to see if the agent is able to have an infinite context
for x in range(0,10000):
    response = handler.chain('What happened next? Remember to spin it out for infinity!')
    print(response)