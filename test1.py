from dataclasses import dataclass, asdict
from typing import Optional, Dict, Any, List
import requests
from contextlib import contextmanager

@dataclass
class LLMConfig:
    llm_name: str
    max_gpu_memory: dict | None = None
    eval_device: str = "cuda:0"
    max_new_tokens: int = 2048
    log_mode: str = "console"
    use_backend: str = "default"

@dataclass
class StorageConfig:
    root_dir: str = "root"
    use_vector_db: bool = False
    vector_db_config: Optional[Dict[str, Any]] = None

@dataclass
class MemoryConfig:
    memory_limit: int = 104857600  # 100MB
    eviction_k: int = 10
    custom_eviction_policy: Optional[str] = None

@dataclass
class ToolManagerConfig:
    allowed_tools: Optional[List[str]] = None
    custom_tools: Optional[Dict[str, Any]] = None

@dataclass
class SchedulerConfig:
    log_mode: str = "console"
    max_workers: int = 64
    custom_syscalls: Optional[Dict[str, Any]] = None

class AIOSCoreClient:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url.rstrip('/')
        self._components_initialized = set()

    def _post(self, endpoint: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Make a POST request to the specified endpoint."""
        response = requests.post(f"{self.base_url}{endpoint}", json=data)
        response.raise_for_status()
        return response.json()

    def _get(self, endpoint: str) -> Dict[str, Any]:
        """Make a GET request to the specified endpoint."""
        response = requests.get(f"{self.base_url}{endpoint}")
        response.raise_for_status()
        return response.json()

    def setup_llm(self, config: LLMConfig) -> Dict[str, Any]:
        """Set up the LLM core component."""
        result = self._post("/core/llm/setup", asdict(config))
        self._components_initialized.add("llm")
        return result

    def setup_storage(self, config: StorageConfig) -> Dict[str, Any]:
        """Set up the storage manager component."""
        result = self._post("/core/storage/setup", asdict(config))
        self._components_initialized.add("storage")
        return result

    def setup_memory(self, config: MemoryConfig) -> Dict[str, Any]:
        """Set up the memory manager component."""
        if "storage" not in self._components_initialized:
            raise ValueError("Storage manager must be initialized before memory manager")
        
        result = self._post("/core/memory/setup", asdict(config))
        self._components_initialized.add("memory")
        return result

    def setup_tool_manager(self, config: ToolManagerConfig) -> Dict[str, Any]:
        """Set up the tool manager component."""
        result = self._post("/core/tool/setup", asdict(config))
        self._components_initialized.add("tool")
        return result

    def setup_agent_factory(self, config: SchedulerConfig) -> Dict[str, Any]:
        """Set up the agent factory for managing agent execution."""
        required_components = {"llm", "memory", "storage", "tool"}
        missing_components = required_components - self._components_initialized
        
        if missing_components:
            raise ValueError(
                f"Missing required components: {', '.join(missing_components)}"
            )
        
        result = self._post("/core/factory/setup", asdict(config))
        self._components_initialized.add("factory")
        return result
        
    def submit_agent(self, agent_id: str, agent_config: Dict[str, Any]) -> Dict[str, Any]:
        """Submit an agent for execution."""
        if "factory" not in self._components_initialized:
            raise ValueError("Agent factory must be initialized before submitting agents")
        
        return self._post("/agents/submit", {
            "agent_id": agent_id,
            "agent_config": agent_config
        })

    def get_agent_status(self, execution_id: str) -> Dict[str, Any]:
        """Get the status of a submitted agent."""
        if "factory" not in self._components_initialized:
            raise ValueError("Agent factory must be initialized before checking agent status")
        
        return self._get(f"/agents/{execution_id}/status")

    def wait_for_agent(self, execution_id: str, polling_interval: float = 1.0, timeout: Optional[float] = None) -> Dict[str, Any]:
        """Wait for an agent to complete execution."""
        import time
        start_time = time.time()
        
        while True:
            status = self.get_agent_status(execution_id)
            if status["status"] == "completed":
                return status["result"]
            
            if timeout and (time.time() - start_time) > timeout:
                raise TimeoutError(f"Agent execution {execution_id} did not complete within {timeout} seconds")
            
            time.sleep(polling_interval)

    def setup_scheduler(self, config: SchedulerConfig) -> Dict[str, Any]:
        """Set up the FIFO scheduler with all components."""
        required_components = {"llm", "memory", "storage", "tool"}
        missing_components = required_components - self._components_initialized
        
        if missing_components:
            raise ValueError(
                f"Missing required components: {', '.join(missing_components)}"
            )
        
        result = self._post("/core/scheduler/setup", asdict(config))
        self._components_initialized.add("scheduler")
        return result

    def get_status(self) -> Dict[str, str]:
        """Get the status of all core components."""
        return self._get("/core/status")

    def cleanup(self) -> Dict[str, Any]:
        """Clean up all active components."""
        result = self._post("/core/cleanup", {})
        self._components_initialized.clear()
        return result

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cleanup()

@contextmanager
def aios_core_setup(
    llm_config: LLMConfig,
    storage_config: Optional[StorageConfig] = None,
    memory_config: Optional[MemoryConfig] = None,
    tool_config: Optional[ToolManagerConfig] = None,
    scheduler_config: Optional[SchedulerConfig] = None,
    base_url: str = "http://localhost:8000"
) -> AIOSCoreClient:
    """
    Context manager for setting up all AIOS core components.
    
    Example:
        with aios_core_setup(
            llm_config=LLMConfig(llm_name="gpt-3.5-turbo"),
            storage_config=StorageConfig(root_dir="my_storage"),
            memory_config=MemoryConfig(memory_limit=200*1024*1024)
        ) as core:
            # Use the initialized core components
            status = core.get_status()
            print(status)
    """
    client = AIOSCoreClient(base_url)
    
    try:
        # Set up components in order of dependency
        client.setup_llm(llm_config)
        
        if storage_config:
            client.setup_storage(storage_config)
        else:
            client.setup_storage(StorageConfig())
            
        if memory_config:
            client.setup_memory(memory_config)
        else:
            client.setup_memory(MemoryConfig())
            
        if tool_config:
            client.setup_tool_manager(tool_config)
        else:
            client.setup_tool_manager(ToolManagerConfig())
            
        if scheduler_config:
            client.setup_scheduler(scheduler_config)
        else:
            client.setup_scheduler(SchedulerConfig())
            
        yield client
    finally:
        client.cleanup()

# Example usage:
if __name__ == "__main__":
    # Example 1: Using the context manager
    # with aios_core_setup(
    #     llm_config=LLMConfig(
    #         llm_name="gpt-3.5-turbo",
    #         max_gpu_memory="16GiB"
    #     ),
    #     storage_config=StorageConfig(
    #         root_dir="my_project",
    #         use_vector_db=True
    #     ),
    #     memory_config=MemoryConfig(
    #         memory_limit=200*1024*1024,  # 200MB
    #         eviction_k=20
    #     )
    # ) as core:
    #     status = core.get_status()
    #     print("Core components status:", status)
    
    # Example 2: Manual setup
    client = AIOSCoreClient()
    try:
        # Set up components one by one
        client.setup_llm(LLMConfig(llm_name="gemini-1.5-flash"))
        client.setup_storage(StorageConfig(root_dir="root"))
        client.setup_memory(MemoryConfig(memory_limit=500*1024*1024))
        client.setup_tool_manager(ToolManagerConfig(
            allowed_tools=["python", "shell", "browser"]
        ))
        client.setup_scheduler(SchedulerConfig(max_workers=32))
        
        # Check status
        status = client.get_status()
        print("Manually initialized components:", status)

        client.setup_agent_factory(SchedulerConfig(max_workers=64))

        result = client.submit_agent("example/academic_agent", {
            "task": "Tell me what is the prollm paper mainly about? ",
        })

        # Wait for completion
        try:
            final_result = client.wait_for_agent(
                result["execution_id"],
                timeout=300  # 5 minutes timeout
            )
            print("Agent completed:", final_result)
        except TimeoutError:
            print("Agent execution timed out")
    finally:
        client.cleanup()