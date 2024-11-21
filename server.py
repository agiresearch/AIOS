from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any
import uvicorn
from contextlib import asynccontextmanager

from aios.hooks.modules.llm import useCore
from aios.hooks.modules.memory import useMemoryManager
from aios.hooks.modules.storage import useStorageManager
from aios.hooks.modules.tool import useToolManager
from aios.hooks.modules.agent import useFactory
from aios.hooks.modules.scheduler import fifo_scheduler_nonblock as fifo_scheduler

app = FastAPI()

# Store component configurations and instances
active_components = {
    "llm": None,
    "storage": None,
    "memory": None,
    "tool": None,
    "scheduler": None
}

class LLMConfig(BaseModel):
    llm_name: str
    max_gpu_memory: dict | None = None 
    eval_device: str = "cuda:0"
    max_new_tokens: int = 2048
    log_mode: str = "INFO"
    use_backend: str = "default"

class StorageConfig(BaseModel):
    root_dir: str = "root"
    use_vector_db: bool = False
    vector_db_config: Optional[Dict[str, Any]] = None

class MemoryConfig(BaseModel):
    memory_limit: int = 104857600  # 100MB in bytes
    eviction_k: int = 10
    custom_eviction_policy: Optional[str] = None

class ToolManagerConfig(BaseModel):
    allowed_tools: Optional[list[str]] = None
    custom_tools: Optional[Dict[str, Any]] = None

class SchedulerConfig(BaseModel):
    log_mode: str = "INFO"
    max_workers: int = 64
    custom_syscalls: Optional[Dict[str, Any]] = None

@app.post("/core/llm/setup")
async def setup_llm(config: LLMConfig):
    """Set up the LLM core component."""
    # try:
    #     llm = useCore(
    #         llm_name=config.llm_name,
    #         max_gpu_memory=config.max_gpu_memory,
    #         eval_device=config.eval_device,
    #         max_new_tokens=config.max_new_tokens,
    #         log_mode=config.log_mode,
    #         use_backend=config.use_backend
    #     )
    #     active_components["llm"] = llm
    #     return {"status": "success", "message": "LLM core initialized"}
    # except Exception as e:
    #     print(e)

    #     raise HTTPException(status_code=500, detail=f"Failed to initialize LLM core: {str(e)}")
    llm = useCore(
            llm_name=config.llm_name,
            max_gpu_memory=config.max_gpu_memory,
            eval_device=config.eval_device,
            max_new_tokens=config.max_new_tokens,
            log_mode=config.log_mode,
            use_backend=config.use_backend
        )
    active_components["llm"] = llm
    return {"status": "success", "message": "LLM core initialized"}

@app.post("/core/storage/setup")
async def setup_storage(config: StorageConfig):
    """Set up the storage manager component."""
    try:
        storage_manager = useStorageManager(
            root_dir=config.root_dir,
            use_vector_db=config.use_vector_db,
            **(config.vector_db_config or {})
        )
        active_components["storage"] = storage_manager
        return {"status": "success", "message": "Storage manager initialized"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to initialize storage manager: {str(e)}")

@app.post("/core/memory/setup")
async def setup_memory(config: MemoryConfig):
    """Set up the memory manager component."""
    if not active_components["storage"]:
        raise HTTPException(status_code=400, detail="Storage manager must be initialized first")

    try:
        memory_manager = useMemoryManager(
            memory_limit=config.memory_limit,
            eviction_k=config.eviction_k,
            storage_manager=active_components["storage"]
        )
        active_components["memory"] = memory_manager
        return {"status": "success", "message": "Memory manager initialized"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to initialize memory manager: {str(e)}")

@app.post("/core/tool/setup")
async def setup_tool_manager(config: ToolManagerConfig):
    """Set up the tool manager component."""
    try:
        tool_manager = useToolManager()

        active_components["tool"] = tool_manager
        return {"status": "success", "message": "Tool manager initialized"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to initialize tool manager: {str(e)}")

@app.post("/core/factory/setup")
async def setup_agent_factory(config: SchedulerConfig):
    """Set up the agent factory for managing agent execution."""
    required_components = ["llm", "memory", "storage", "tool"]
    missing_components = [comp for comp in required_components if not active_components[comp]]

    if missing_components:
        raise HTTPException(
            status_code=400,
            detail=f"Missing required components: {', '.join(missing_components)}"
        )

    try:
        submit_agent, await_agent_execution = useFactory(
            log_mode=config.log_mode,
            max_workers=config.max_workers
        )

        active_components["factory"] = {
            "submit": submit_agent,
            "await": await_agent_execution
        }

        print(active_components['llm'].model)

        return {"status": "success", "message": "Agent factory initialized"}
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail=f"Failed to initialize agent factory: {str(e)}")

@app.post("/core/scheduler/setup")
async def setup_scheduler(config: SchedulerConfig):
    """Set up the FIFO scheduler with all components."""
    required_components = ["llm", "memory", "storage", "tool"]
    missing_components = [comp for comp in required_components if not active_components[comp]]

    if missing_components:
        raise HTTPException(
            status_code=400,
            detail=f"Missing required components: {', '.join(missing_components)}"
        )

    try:
        # Set up the scheduler with all components
        scheduler = fifo_scheduler(
            llm=active_components["llm"],
            memory_manager=active_components["memory"],
            storage_manager=active_components["storage"],
            tool_manager=active_components["tool"],
            log_mode=config.log_mode,
            get_llm_syscall=None,
            get_memory_syscall=None,
            get_storage_syscall=None,
            get_tool_syscall=None
            # **(config.custom_syscalls or {})
        )

        active_components["scheduler"] = scheduler

        scheduler.start()

        return {"status": "success", "message": "Scheduler initialized"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to initialize scheduler: {str(e)}")

@app.get("/core/status")
async def get_status():
    """Get the status of all core components."""
    return {
        component: "active" if instance else "inactive"
        for component, instance in active_components.items()
    }

class AgentSubmit(BaseModel):
    agent_id: str
    agent_config: Dict[str, Any]

@app.post("/agents/submit")
async def submit_agent(config: AgentSubmit):
    """Submit an agent for execution using the agent factory."""
    if "factory" not in active_components or not active_components["factory"]:
        raise HTTPException(
            status_code=400,
            detail="Agent factory not initialized"
        )

    try:
        _submit_agent = active_components["factory"]["submit"]
        execution_id = _submit_agent(agent_name=config.agent_id, task_input=config.agent_config['task'])
        print(execution_id)

        return {
            "status": "success",
            "execution_id": execution_id,
            "message": f"Agent {config.agent_id} submitted for execution"
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to submit agent: {str(e)}"
        )

@app.get("/agents/{execution_id}/status")
async def get_agent_status(execution_id: int):
    """Get the status of a submitted agent."""
    if "factory" not in active_components or not active_components["factory"]:
        raise HTTPException(
            status_code=400,
            detail="Agent factory not initialized"
        )

    try:
        await_execution = active_components["factory"]["await"]
        result = await_execution(int(execution_id))

        return {
            "status": "completed",
            "result": result
        }
    except Exception as e:
        print(e)
        return {
            "status": "running",
            "message": str(e)
        }

@app.post("/core/cleanup")
async def cleanup_components():
    """Clean up all active components."""
    try:
        # Clean up in reverse order of dependency
        active_components["scheduler"].stop()
        active_components["scheduler"] = None

        for component in ["tool", "memory", "storage", "llm"]:
            if active_components[component]:
                if hasattr(active_components[component], "cleanup"):
                    active_components[component].cleanup()
                active_components[component] = None





        return {"status": "success", "message": "All components cleaned up"}
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail=f"Failed to cleanup components: {str(e)}")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)