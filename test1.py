from dataclasses import dataclass, asdict
from typing import Optional, Dict, Any, List
import requests
from contextlib import contextmanager


from cerebrum.client import Cerebrum
from cerebrum.llm.layer import LLMLayer
from cerebrum.memory.layer import MemoryLayer
from cerebrum.overrides.layer import OverridesLayer
from cerebrum.storage.layer import StorageLayer
from cerebrum.tool.layer import ToolLayer


# Example usage:
if __name__ == "__main__":
   
    client = Cerebrum()
    try:
        # Set up components one by one
        client.add_llm_layer(LLMLayer(llm_name="gemini-1.5-flash")) \
              .add_storage_layer(StorageLayer(root_dir="root")) \
              .add_memory_layer(MemoryLayer(memory_limit=500*1024*1024)) \
              .add_tool_layer(ToolLayer()) \
              .override_scheduler(OverridesLayer(max_works=32))
        
        # Check status
        status = client.get_status()
        print("Manually initialized components:", status)

        client.connect()

        result = client.execute("example/academic_agent", {
            "task": "Tell me what is the prollm paper mainly about? ",
        })

        # Wait for completion
        try:
            final_result = client.poll_agent(
                result["execution_id"],
                timeout=300  # 5 minutes timeout
            )
            print("Agent completed:", final_result)
        except TimeoutError:
            print("Agent execution timed out")
    finally:
        client.cleanup()