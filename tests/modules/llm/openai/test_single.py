import unittest
from cerebrum.llm.apis import llm_chat, llm_chat_with_json_output
from cerebrum.utils.communication import aios_kernel_url
from cerebrum.utils.utils import _parse_json_output

class TestAgent:
    """
    TestAgent class is responsible for interacting with OpenAI's API using ChatCompletion.
    It maintains a conversation history to simulate real dialogue behavior.
    """
    def __init__(self, agent_name):
        self.agent_name = agent_name
        self.messages = []

    def llm_chat_run(self, task_input):
        """Sends the input to the OpenAI API and returns the response."""
        self.messages.append({"role": "user", "content": task_input})

        tool_response = llm_chat(
            agent_name=self.agent_name,
            messages=self.messages,
            base_url=aios_kernel_url,
            llms=[{
                "name": "gpt-4o-mini",
                "backend": "openai"
            }]
        )

        return tool_response["response"].get("response_message", "")
    
    def llm_chat_with_json_output_run(self, task_input):
        """Sends the input to the OpenAI API and returns the response."""
        self.messages.append({"role": "user", "content": task_input})

        response_format = {
            "type": "json_schema",
            "json_schema": {
                "name": "thinking",
                "schema": {
                    "type": "object",
                    "properties": {
                        "thinking": {
                            "type": "string",
                        },
                        "answer": {
                            "type": "string",
                        }
                    }
                }
            }
        }

        tool_response = llm_chat_with_json_output(
            agent_name=self.agent_name,
            messages=self.messages,
            base_url=aios_kernel_url,
            llms=[{
                "name": "gpt-4o-mini",
                "backend": "openai"
            }],
            response_format=response_format
        )

        return tool_response["response"].get("response_message", "")


class TestLLMAPI(unittest.TestCase):
    """
    Unit tests for OpenAI's API using the TestAgent class.
    Each test checks if the API returns a non-empty string response.
    Here has various category test cases, including greeting, math question, science question, history question, technology question.
    """
    def setUp(self):
        self.agent = TestAgent("test_agent")

    def assert_chat_response(self, response):
        """Helper method to validate common response conditions."""
        self.assertIsInstance(response, str)
        self.assertGreater(len(response), 0)
        
    def assert_json_output_response(self, response):
        """Helper method to validate common response conditions."""
        parsed_response = _parse_json_output(response)
        self.assertIsInstance(parsed_response, dict)
        self.assertIn("thinking", parsed_response)
        self.assertIn("answer", parsed_response)
        self.assertIsInstance(parsed_response["thinking"], str)
        self.assertIsInstance(parsed_response["answer"], str)

    def test_agent_with_greeting(self):
        chat_response = self.agent.llm_chat_run("Hello, how are you?")
        self.assert_chat_response(chat_response)
        json_output_response = self.agent.llm_chat_with_json_output_run("Hello, how are you? Output in JSON format of {{'thinking': 'your thinking', 'answer': 'your answer'}}.")
        self.assert_json_output_response(json_output_response)

    def test_agent_with_math_question(self):
        chat_response = self.agent.llm_chat_run("What is 25 times 4?")
        self.assert_chat_response(chat_response)
        json_output_response = self.agent.llm_chat_with_json_output_run("What is 25 times 4? Output in JSON format of {{'thinking': 'your thinking', 'answer': 'your answer'}}.")
        self.assert_json_output_response(json_output_response)


    def test_agent_with_history_question(self):
        chat_response = self.agent.llm_chat_run("Who was the first president of the United States?")
        self.assert_chat_response(chat_response)
        json_output_response = self.agent.llm_chat_with_json_output_run("Who was the first president of the United States? Output in JSON format of {{'thinking': 'your thinking', 'answer': 'your answer'}}.")
        self.assert_json_output_response(json_output_response)

    def test_agent_with_technology_question(self):
        chat_response = self.agent.llm_chat_run("What is quantum computing?")
        self.assert_chat_response(chat_response)
        json_output_response = self.agent.llm_chat_with_json_output_run("What is quantum computing? Output in JSON format of {{'thinking': 'your thinking', 'answer': 'your answer'}}.")
        self.assert_json_output_response(json_output_response)


if __name__ == "__main__":
    unittest.main()
