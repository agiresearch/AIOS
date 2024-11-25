from cerebrum import config
from cerebrum.client import Cerebrum
from cerebrum.llm.layer import LLMLayer
from cerebrum.memory.layer import MemoryLayer
from cerebrum.overrides.layer import OverridesLayer
from cerebrum.storage.layer import StorageLayer
from cerebrum.tool.layer import ToolLayer


# Example usage:
if __name__ == "__main__":

    client = Cerebrum()

    config.global_client = client

    try:
        # Set up components one by one
        client.add_llm_layer(
            LLMLayer(llm_name="gpt-4o-mini", use_backend="openai")
        ).add_storage_layer(StorageLayer(root_dir="root")).add_memory_layer(
            MemoryLayer(memory_limit=500 * 1024 * 1024)
        ).add_tool_layer(
            ToolLayer()
        ).override_scheduler(
            OverridesLayer(max_workers=32)
        )

        # Check status
        status = client.get_status()
        print("Manually initialized components:", status)

        client.connect()

        tasks = [
            ["example/academic_agent", {"task": "Tell me what is the aios paper mainly about? ",}],
            ["example/academic_agent", {"task": "Search openagi related papers? ",}],
        ]
        results = []
        for task in tasks:
            result = client.execute(
                task[0], task[1]
            )
            results.append(result)

        # Wait for completion
        try:
            for result in results:
                final_result = client.poll_agent(
                    result["execution_id"], timeout=300  # 5 minutes timeout
                )
                print(final_result)
        except TimeoutError:
            print("Agent execution timed out")
    finally:
        client.cleanup()
