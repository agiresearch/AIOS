# test_client.py
import requests
import threading
import json
import time

# Assume the server is running on localhost:8000 based on launch.py default
BASE_URL = "http://localhost:8000"
QUERY_ENDPOINT = f"{BASE_URL}/query"

# --- Define Payloads for the two concurrent requests ---

# Payload 1: Example LLM Query
# Note: Adjust 'agent_name', 'llms', and 'messages' based on your actual setup
payload1 = {
    "agent_name": "test_agent_1",
    "query_type": "llm",
    "query_data": {
        "messages": [{"role": "user", "content": "What is the capital of France?"}],
        "action_type": "chat",
        "message_return_type": "text",
    }
}

# Payload 2: Example Storage Query
# Note: Adjust 'agent_name', 'operation_type', and 'params' based on your actual setup
payload2 = {
    "agent_name": "test_agent_2",
    "query_type": "llm",
    "query_data": {
        "messages": [{"role": "user", "content": "What is the capital of United States?"}],
        "action_type": "chat",
        "message_return_type": "text",
    }
}

# List of payloads for the requests
payloads = [payload1, payload2]
responses = [None] * len(payloads) # To store responses

# --- Function to send a single request ---
def send_request(index, payload):
    """Sends a POST request to the query endpoint and stores the response."""
    global responses
    try:
        print(f"Thread {index}: Sending request with payload: {json.dumps(payload)}")
        start_time = time.time()
        response = requests.post(QUERY_ENDPOINT, json=payload)
        end_time = time.time()
        response.raise_for_status() # Raise an exception for bad status codes (4xx or 5xx)
        responses[index] = response.json()
        print(f"Thread {index}: Received response (Status: {response.status_code}) in {end_time - start_time:.2f}s.")
        # print(f"Thread {index}: Response data: {responses[index]}")
    except requests.exceptions.RequestException as e:
        print(f"Thread {index}: Request failed: {e}")
        if e.response is not None:
            print(f"Thread {index}: Server response: {e.response.text}")
        responses[index] = {"error": str(e)}
    except Exception as e:
        print(f"Thread {index}: An unexpected error occurred: {e}")
        responses[index] = {"error": f"Unexpected error: {str(e)}"}

# --- Create and start threads ---
threads = []
print(f"Sending {len(payloads)} concurrent requests to {QUERY_ENDPOINT}...")

for i, payload in enumerate(payloads):
    thread = threading.Thread(target=send_request, args=(i, payload))
    threads.append(thread)
    thread.start()

# --- Wait for all threads to complete ---
for i, thread in enumerate(threads):
    thread.join()
    print(f"Thread {i} finished.")

# --- Print all responses ---
print("\n--- All Responses ---")
for i, response_data in enumerate(responses):
    print(f"Response from request {i}:")
    print(json.dumps(response_data, indent=2))
    print("-" * 20)

print("All requests completed.")