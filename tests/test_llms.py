import sys

import os

from src.llms.llms import LLMKernel
from src.llms.llm_config import LLMMeta

def test_closed_llm():
    llm_type = "gemini-pro"
    llm = LLMKernel(llm_type)
    prompt = "Craft a tale about a valiant warrior on a quest to uncover priceless treasures hidden within a mystical island."
    response = llm.address_request(prompt)
    assert isinstance(response, str)
    print(response)
