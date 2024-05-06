import sys

import os

from src.llm_kernel.llms import LLMKernel

from openagi.src.agents.agent_process import AgentProcess

from src.context.simple_context import SimpleContextManager

def test_closed_llm():
    # if "GEMINI_API_KEY" not in os.environ or not os.environ["RAPID_API_KEY"]:
    #     with pytest.raises(ValueError):
    #         llm_type = "gemini-pro"
    #         llm = LLMKernel(llm_type)
    llm_type = "gemini-pro"
    llm = LLMKernel(llm_type)
    agent_process = AgentProcess(
        agent_name = "Narrative Agent",
        prompt = "Craft a tale about a valiant warrior on a quest to uncover priceless treasures hidden within a mystical island."
    )
    llm.address_request(agent_process)
    print(agent_process.get_response())
    assert isinstance(agent_process.get_response(), str)
    # print(response)

def test_open_llm():
    llm_type = "gemma-2b-it"
    max_gpu_memory = {"4": "48GB"}
    eval_device = "cuda:4"
    max_new_tokens = 256
    llm = LLMKernel(
        llm_type,
        max_gpu_memory=max_gpu_memory,
        eval_device=eval_device,
        max_new_tokens=max_new_tokens
    )
    agent_process = AgentProcess(
        agent_name = "Narrative Agent",
        prompt = "Craft a tale about a valiant warrior on a quest to uncover priceless treasures hidden within a mystical island."
    )
    context_manager = SimpleContextManager()
    agent_process.set_pid(0)
    agent_process.set_time_limit(1)
    llm.address_request(agent_process)
    assert context_manager.check_restoration(0) is True
    context_manager.clear_restoration(0)
