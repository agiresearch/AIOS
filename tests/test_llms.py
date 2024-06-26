# This gives sample prompts to the LLMs to make sure they are working. This 
# file will require a lot of API keys for each closed LLM.

import torch
import pytest
from dotenv import load_dotenv, find_dotenv
from src.llm_kernel.llms import LLMKernel
from openagi.src.agents.agent_process import AgentProcess
from src.context.simple_context import SimpleContextManager

from src.utils.message import Message

# Load environment variables once for all tests
load_dotenv(find_dotenv())

@pytest.fixture
def llm_setup():
    if torch.cuda.device_count() > 0:
        llm_type = "gemma-2b-it"
        max_gpu_memory = {"4": "48GB"}
        eval_device = "cuda:4"
        max_new_tokens = 10
        llm = LLMKernel(llm_type, max_gpu_memory=max_gpu_memory, eval_device=eval_device, max_new_tokens=max_new_tokens)
    else:
        llm_type = "ollama/llama3"
        max_new_tokens = 10
        llm = LLMKernel(llm_type, max_new_tokens=max_new_tokens)
    return llm

def test_closed_llm():
    llm_type = "gemini-pro"
    llm = LLMKernel(llm_type, max_new_tokens = 10)
    agent_process = AgentProcess(
        agent_name="Narrative Agent",
        message = Message(
            prompt="Craft a tale about a valiant warrior on a quest to uncover priceless treasures hidden within a mystical island."
        )
    )
    llm.address_request(agent_process)
    response = agent_process.get_response()
    assert isinstance(response.response_message, str), "The response should be a string"

def test_open_llm(llm_setup):
    llm = llm_setup
    agent_process = AgentProcess(
        agent_name="Narrative Agent",
        message = Message(
            prompt="Craft a tale about a valiant warrior on a quest to uncover priceless treasures hidden within a mystical island."
        )
    )
    llm.address_request(agent_process)
    response = agent_process.get_response()
    assert isinstance(response.response_message, str), "The response should be a string"
    if torch.cuda.device_count() > 0:
        context_manager = SimpleContextManager()
        agent_process.set_pid(0)
        agent_process.set_time_limit(1)
        llm.address_request(agent_process)
        assert context_manager.check_restoration(0), "Restoration should be successful"
        context_manager.clear_restoration(0)
