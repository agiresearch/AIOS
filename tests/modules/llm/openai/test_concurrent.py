# test_client.py
import unittest
import requests
import threading
import json
import time
from typing import List, Dict, Any, Tuple

from cerebrum.llm.apis import llm_chat

from cerebrum.utils.communication import aios_kernel_url

# --- Helper function to send a single request ---
def send_request(payload: Dict[str, Any]) -> Tuple[Dict[str, Any] | None, float]:
    """Sends a POST request to the query endpoint and returns status code, response JSON, and duration."""
    start_time = time.time()
    try:
        response = llm_chat(
            agent_name=payload["agent_name"],
            messages=payload["query_data"]["messages"],
            llms=payload["query_data"]["llms"] if "llms" in payload["query_data"] else None,
        )
        end_time = time.time()
        duration = end_time - start_time
        return response["response"], duration
    
    except Exception as e:
        end_time = time.time()
        duration = end_time - start_time
        # General unexpected errors
        return {"error": f"An unexpected error occurred: {e}"}, duration


class TestConcurrentLLMQueries(unittest.TestCase):

    def _run_concurrent_requests(self, payloads: List[Dict[str, Any]]):
        results = [None] * len(payloads)
        threads = []

        def worker(index, payload):
            response_data, duration = send_request(payload)
            results[index] = {"data": response_data, "duration": duration}
            print(f"Thread {index}: Completed in {duration:.2f}s with response: {json.dumps(response_data)}")

        print(f"\n--- Running test: {self._testMethodName} ---")
        print(f"Sending {len(payloads)} concurrent requests to {aios_kernel_url}...")
        for i, payload in enumerate(payloads):
            thread = threading.Thread(target=worker, args=(i, payload))
            threads.append(thread)
            thread.start()

        for i, thread in enumerate(threads):
            thread.join()
            print(f"Thread {i} finished.")

        print("--- All threads completed ---")
        return results

    def test_both_llms(self):
        payload1 = {
            "agent_name": "test_agent_1",
            "query_type": "llm",
            "query_data": {
                "llms": [{"name": "gpt-4o", "backend": "openai"}],
                "messages": [{"role": "user", "content": "What is the capital of France?"}],
                "action_type": "chat",
                "message_return_type": "text",
            }
        }
        payload2 = {
            "agent_name": "test_agent_2",
            "query_type": "llm",
            "query_data": {
                "llms": [{"name": "gpt-4o-mini", "backend": "openai"}], # Using a different model for variety
                "messages": [{"role": "user", "content": "What is the capital of the United States?"}],
                "action_type": "chat",
                "message_return_type": "text",
            }
        }
        results = self._run_concurrent_requests([payload1, payload2])
        
        for i, result in enumerate(results):
            print(f"Result {i} (No LLM): {result}")
            # Both should succeed using defaults
            status, response_message, error_message, finished = result["data"]["status_code"], result["data"]["response_message"], result["data"]["error"], result["data"]["finished"]
            
            self.assertEqual(status, 200, f"Request {i} (No LLM) should succeed, but failed with status {status}")
            self.assertIsNone(error_message, f"Request {i} (No LLM) returned an unexpected error: {error_message}")
            self.assertIsInstance(response_message, str, f"Request {i} (No LLM) result is not a string")
            self.assertTrue(finished, f"Request {i} (No LLM) result is empty") # Check not empty

    def test_one_llm_one_empty(self):
        payload_llm = {
            "agent_name": "test_agent_1",
            "query_type": "llm",
            "query_data": {
                "llms": [{"name": "gpt-4o", "backend": "openai"}],
                "messages": [{"role": "user", "content": "What is the capital of France?"}],
                "action_type": "chat",
                "message_return_type": "text",
            }
        }
        payload_no_llm = {
            "agent_name": "test_agent_2",
            "query_type": "llm",
            "query_data": {
                # 'llms' key is omitted entirely
                "messages": [{"role": "user", "content": "What is the capital of the United States?"}],
                "action_type": "chat",
                "message_return_type": "text",
            }
        }
        results = self._run_concurrent_requests([payload_llm, payload_no_llm])
        
        for i, result in enumerate(results):
            print(f"Result {i} (No LLM): {result}")
            # Both should succeed using defaults
            status, response_message, error_message, finished = result["data"]["status_code"], result["data"]["response_message"], result["data"]["error"], result["data"]["finished"]
            
            self.assertEqual(status, 200, f"Request {i} (No LLM) should succeed, but failed with status {status}")
            self.assertIsNone(error_message, f"Request {i} (No LLM) returned an unexpected error: {error_message}")
            self.assertIsInstance(response_message, str, f"Request {i} (No LLM) result is not a string")
            self.assertTrue(finished, f"Request {i} (No LLM) result is empty") # Check not empty

    def test_no_llms(self):
        """Case 2: Both payloads have no LLMs defined. Should succeed using defaults."""
        payload1 = {
            "agent_name": "test_agent_1",
            "query_type": "llm",
            "query_data": {
                # 'llms' key is omitted
                "messages": [{"role": "user", "content": "What is the capital of France?"}],
                "action_type": "chat",
                "message_return_type": "text",
            }
        }
        payload2 = {
            "agent_name": "test_agent_2",
            "query_type": "llm",
            "query_data": {
                # 'llms' key is omitted
                "messages": [{"role": "user", "content": "What is the capital of the United States?"}],
                "action_type": "chat",
                "message_return_type": "text",
            }
        }
        results = self._run_concurrent_requests([payload1, payload2])
        
        for i, result in enumerate(results):
            print(f"Result {i} (No LLM): {result}")
            # Both should succeed using defaults
            status, response_message, error_message, finished = result["data"]["status_code"], result["data"]["response_message"], result["data"]["error"], result["data"]["finished"]
            
            self.assertEqual(status, 200, f"Request {i} (No LLM) should succeed, but failed with status {status}")
            self.assertIsNone(error_message, f"Request {i} (No LLM) returned an unexpected error: {error_message}")
            self.assertIsInstance(response_message, str, f"Request {i} (No LLM) result is not a string")
            self.assertTrue(finished, f"Request {i} (No LLM) result is empty") # Check not empty


if __name__ == '__main__':
    unittest.main()