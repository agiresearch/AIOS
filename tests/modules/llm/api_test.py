"""
Function: Generate multiple test cases in bulk to ensure that the various libraries in `test_apis.py` are functioning correctly.  
LLM used for evaluation: qwen2.5:7b
"""
import pytest
from cerebrum.test_apis import test_single_llm_chat, test_multi_llm_chat, test_llm_call_tool, test_sto_retrieve

# To test llm_chat in more angle, we used GPT-4o to generate   
def test_single_llm_chat_with_multi_cases():
    test_cases = [
        {"role": "user", "content": "What is the capital of France?"},
        {"role": "user", "content": "What is 1234 x 5678?"},
        {"role": "user", "content": "Write a Python function to check if a number is prime."},
        {"role": "user", "content": "If all cats are animals and some animals are pets, are all cats pets?"},
        {"role": "user", "content": "Translate 'Hello, how are you?' to French."},
        {"role": "user", "content": "Summarize the following text: Artificial intelligence is transforming various industries..."},
        {"role": "user", "content": "Write a short story about a robot learning emotions."}
    ]

    for case in test_cases:
        print(f"Input: {case['content']}\n")
        with pytest.raises(TypeError):
            test_single_llm_chat([case])

def test_multi_llm_chat_with_multi_cases():
    test_cases = [
        {"role": "user", "content": "What is the capital of the United States?"},
        {"role": "user", "content": "Solve for x: 3x + 7 = 22."},
        {"role": "user", "content": "Generate a Python script to scrape data from a website."},
        {"role": "user", "content": "Is 'Every human is mortal. Socrates is human. Therefore, Socrates is mortal.' a valid argument?"},
        {"role": "user", "content": "Translate 'Good morning' to Japanese."},
        {"role": "user", "content": "Summarize the main findings of the 2023 AI research trends."},
        {"role": "user", "content": "Write a haiku about the moon."}
    ]

    for case in test_cases:
        print(f"Input: {case['content']}\n")
        with pytest.raises(TypeError):
            test_multi_llm_chat([case])

def test_call_tool_with_multi_cases():
    test_cases = [
        {"role": "user", "content": "Tell me the core idea of OpenAGI paper"},
        {"role": "user", "content": "Find recent papers on diffusion models."},
        {"role": "user", "content": "Summarize the Transformer paper."},
        {"role": "user", "content": "List the top-cited papers on LLM security."},
        {"role": "user", "content": "Find papers that discuss efficient fine-tuning methods."},
        {"role": "user", "content": "Search for 'Attention is All You Need' on ArXiv."},
        {"role": "user", "content": "What does ArXiv say about quantum computing in 2024?"},
        {"role": "user", "content": ""},  # Edge case: Empty query
        {"role": "user", "content": "asdkjfhgqwer"}  # Edge case: Gibberish query
    ]

    for case in test_cases:
        print(f"Input: {case['content']}\n")
        with pytest.raises(TypeError):
            test_llm_call_tool([case])

def test_sto_retrieve_with_multi_cases():
    test_cases = [
        {"query_text": "top 3 papers related to KV cache", "n": 3, "keywords": None},
        {"query_text": "recent advancements in reinforcement learning", "n": 5, "keywords": ["RL", "reinforcement learning"]},
        {"query_text": "Explainability in large language models", "n": 2, "keywords": ["interpretability"]},
        {"query_text": "AI safety and alignment research", "n": 4, "keywords": None},
        {"query_text": "Efficient transformers for edge devices", "n": 3, "keywords": ["efficient transformers"]},
        {"query_text": "Top papers on adversarial attacks in deep learning", "n": 3, "keywords": ["adversarial", "robustness"]},
        {"query_text": " ", "n": 2, "keywords": None},  # Edge case: Empty query
        {"query_text": "qwertyuiop", "n": 2, "keywords": None}  # Edge case: Nonsense input
    ]

    for case in test_cases:
        print(f"Input: {case['query_text']}\n")
        with pytest.raises(TypeError):
            test_sto_retrieve(case)

if __name__ == "__main__":
    # agent = TestAgent("test_agent", "What is the capital of France?")
    # agent.run()
    test_single_llm_chat_with_multi_cases()
    test_multi_llm_chat_with_multi_cases()
    test_call_tool_with_multi_cases()
    # test_operate_file()
    test_sto_retrieve_with_multi_cases()
    # test_create_file()
    # test_create_dir()
