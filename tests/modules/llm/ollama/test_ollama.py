import unittest
from cerebrum.llm.apis import llm_chat
from cerebrum.utils.communication import aios_kernel_url

class TestAgent:
    """
    TestAgent class is responsible for interacting with the LLM API using llm_chat.
    It maintains a conversation history to simulate real dialogue behavior.
    """
    def __init__(self, agent_name):
        self.agent_name = agent_name
        self.messages = []

    def run(self, task_input):
        """Sends the input to the LLM API and returns the response."""
        self.messages.append({"role": "user", "content": task_input})

        tool_response = llm_chat(
            agent_name=self.agent_name,
            messages=self.messages,
            base_url=aios_kernel_url
        )

        return tool_response["response"].get("response_message", "")


class TestLLMAPI(unittest.TestCase):
    """
    Unit tests for the LLM API using the TestAgent class.
    Each test checks if the API returns a non-empty string response.
    """
    def setUp(self):
        self.agent = TestAgent("test_agent")

    def assert_valid_response(self, response):
        """Helper method to validate common response conditions."""
        self.assertIsInstance(response, str)
        self.assertGreater(len(response), 0)

    def test_agent_with_greeting(self):
        response = self.agent.run("Hello, how are you?")
        self.assert_valid_response(response)

    def test_agent_with_math_question(self):
        response = self.agent.run("What is 25 times 4?")
        self.assert_valid_response(response)

    def test_agent_with_science_question(self):
        response = self.agent.run("Explain the theory of relativity.")
        self.assert_valid_response(response)

    def test_agent_with_history_question(self):
        response = self.agent.run("Who was the first president of the United States?")
        self.assert_valid_response(response)

    def test_agent_with_technology_question(self):
        response = self.agent.run("What is quantum computing?")
        self.assert_valid_response(response)


if __name__ == "__main__":
    unittest.main()
