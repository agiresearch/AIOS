from dataclasses import asdict
from typing import Optional, Dict, Any, List
import requests

from cerebrum.llm.communication import LLMQuery
from cerebrum.overrides.layer import OverridesLayer
from cerebrum.memory.layer import MemoryLayer
from cerebrum.llm.layer import LLMLayer
from cerebrum.tool.layer import ToolLayer
from cerebrum.storage.layer import StorageLayer


class Cerebrum:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url.rstrip('/')
        self._components_initialized = set()
        self.results = {}

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

    def _query_llm(self, agent_name: str, query: LLMQuery):
        result = self._post("/query", {
            'query_type': 'llm',
            'agent_name': agent_name,
            'query_data': query.model_dump()})

        return result

    def add_llm_layer(self, config: LLMLayer) -> 'Cerebrum':
        """Set up the LLM core component."""
        result = self._post("/core/llm/setup", asdict(config))
        self._components_initialized.add("llm")
        self.results['llm'] = result
        return self

    def add_storage_layer(self, config: StorageLayer) -> 'Cerebrum':
        """Set up the storage manager component."""
        result = self._post("/core/storage/setup", asdict(config))
        self._components_initialized.add("storage")
        self.results['storage'] = result
        return self

    def add_memory_layer(self, config: MemoryLayer) -> 'Cerebrum':
        """Set up the memory manager component."""
        if "storage" not in self._components_initialized:
            raise ValueError(
                "Storage manager must be initialized before memory manager")

        result = self._post("/core/memory/setup", asdict(config))
        self._components_initialized.add("memory")
        self.results['memory'] = result
        return self

    def add_tool_layer(self, config: ToolLayer) -> 'Cerebrum':
        """Set up the tool manager component."""
        result = self._post("/core/tool/setup", asdict(config))
        self._components_initialized.add("tool")
        self.results['tool'] = result
        return self

    def setup_agent_factory(self, config: OverridesLayer) -> 'Cerebrum':
        """Set up the agent factory for managing agent execution."""
        required_components = {"llm", "memory", "storage", "tool"}
        missing_components = required_components - self._components_initialized

        if missing_components:
            raise ValueError(
                f"Missing required components: {', '.join(missing_components)}"
            )

        result = self._post("/core/factory/setup", asdict(config))
        self._components_initialized.add("factory")
        self.results['factory'] = result
        return self

    def execute(self, agent_id: str, agent_config: Dict[str, Any]) -> Dict[str, Any]:
        """Submit an agent for execution."""
        if "factory" not in self._components_initialized:
            raise ValueError(
                "Agent factory must be initialized before submitting agents")

        return self._post("/agents/submit", {
            "agent_id": agent_id,
            "agent_config": agent_config
        })

    def get_agent_status(self, execution_id: str) -> Dict[str, Any]:
        """Get the status of a submitted agent."""
        if "factory" not in self._components_initialized:
            raise ValueError(
                "Agent factory must be initialized before checking agent status")

        return self._get(f"/agents/{execution_id}/status")

    def poll_agent(self, execution_id: str, polling_interval: float = 1.0, timeout: Optional[float] = None) -> Dict[str, Any]:
        """Wait for an agent to complete execution."""
        import time
        start_time = time.time()

        while True:
            status = self.get_agent_status(execution_id)
            if status["status"] == "completed":
                return status["result"]

            if timeout and (time.time() - start_time) > timeout:
                raise TimeoutError(
                    f"Agent execution {execution_id} did not complete within {timeout} seconds")

            time.sleep(polling_interval)

    def override_scheduler(self, config: OverridesLayer) -> 'Cerebrum':
        """Set up the FIFO scheduler with all components."""
        required_components = {"llm", "memory", "storage", "tool"}
        missing_components = required_components - self._components_initialized

        if missing_components:
            raise ValueError(
                f"Missing required components: {', '.join(missing_components)}"
            )

        result = self._post("/core/scheduler/setup", asdict(config))
        self._components_initialized.add("scheduler")
        self.results['scheduler'] = result
        return self

    def get_status(self) -> Dict[str, str]:
        """Get the status of all core components."""
        return self._get("/core/status")

    def cleanup(self) -> Dict[str, Any]:
        """Clean up all active components."""
        result = self._post("/core/cleanup", {})
        self._components_initialized.clear()
        return result

    def connect(self) -> 'Cerebrum':
        if (self.results.get('scheduler') is None):
            self.override_scheduler(OverridesLayer(max_workers=32))

        self.setup_agent_factory(OverridesLayer(max_workers=32))

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cleanup()
