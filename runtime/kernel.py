from typing_extensions import Literal
from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel, Field, root_validator
from typing import Optional, Dict, Any, Union
from dotenv import load_dotenv
import traceback
import json
import logging
import yaml
import os

from aios.hooks.modules.llm import useCore
from aios.hooks.modules.memory import useMemoryManager
from aios.hooks.modules.storage import useStorageManager
from aios.hooks.modules.tool import useToolManager
from aios.hooks.modules.agent import useFactory
from aios.hooks.modules.scheduler import fifo_scheduler_nonblock as fifo_scheduler
from aios.hooks.syscall import useSysCall
from aios.config.config_manager import config

from cerebrum.llm.communication import LLMQuery

from cerebrum.memory.communication import MemoryQuery

from cerebrum.tool.communication import ToolQuery

from cerebrum.storage.communication import StorageQuery

from fastapi.middleware.cors import CORSMiddleware

# from cerebrum.llm.layer import LLMLayer as LLMConfig
# from cerebrum.memory.layer import MemoryLayer as MemoryConfig
# from cerebrum.storage.layer import StorageLayer as StorageConfig
# from cerebrum.tool.layer import ToolLayer as ToolManagerConfig

load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Modify this in production!
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Store component configurations and instances
active_components = {
    "llm": None,
    "storage": None,
    "memory": None,
    "tool": None
}

execute_request, SysCallWrapper = useSysCall()

# Configure the root logger
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()  # Output to console
    ]
)

logger = logging.getLogger(__name__)

class LLMConfig(BaseModel):
    llm_name: str
    max_gpu_memory: dict | None = None
    eval_device: str = "cuda:0"
    max_new_tokens: int = 2048
    log_mode: str = "INFO"
    llm_backend: str = "default"
    api_key: str | None = None


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

class AgentSubmit(BaseModel):
    agent_id: str
    agent_config: Dict[str, Any]

class QueryRequest(BaseModel):
    agent_name: str
    query_type: Literal["llm", "tool", "storage", "memory"]
    query_data: LLMQuery | ToolQuery | StorageQuery | MemoryQuery

    @root_validator(pre=True)
    def convert_query_data(cls, values: dict[str, Any]) -> dict[str, Any]:
        if 'query_type' not in values or 'query_data' not in values:
            return values
            
        query_type = values['query_type']
        query_data = values['query_data']
        
        type_mapping = {
            'llm': LLMQuery,
            'tool': ToolQuery,
            'storage': StorageQuery,
            'memory': MemoryQuery
        }
        
        if isinstance(query_data, type_mapping[query_type]):
            return values
            
        if isinstance(query_data, dict):
            values['query_data'] = type_mapping[query_type](**query_data)
            
        return values

def initialize_llm_core(llms_config: dict) -> Any:
    """Initialize LLM core with configuration."""
    try:
        models = llms_config.get("models", [])
        if not models:
            raise ValueError("No LLM models configured")
            
        log_mode = llms_config.get("log_mode", "console")
        model = models[0]  # Currently using first model as default
        
        llm = useCore(
            llm_name=model.get("name"),
            llm_backend=model.get("backend"),
            max_gpu_memory=model.get("max_gpu_memory"),
            eval_device=model.get("eval_device", "cuda:0"),
            max_new_tokens=model.get("max_new_tokens", 256),
            log_mode=log_mode,
        )
        
        if llm:
            print("✅ LLM core initialized")
            return llm
        raise ValueError("LLM core initialization returned None")
        
    except Exception as e:
        print(f"⚠️ Error initializing LLM core: {str(e)}")
        return None

def initialize_storage_manager(storage_config: dict) -> Any:
    """Initialize storage manager with configuration."""
    try:
        storage_manager = useStorageManager(
            root_dir=storage_config.get("root_dir", "root"),
            use_vector_db=storage_config.get("use_vector_db", True),
            **(storage_config.get("vector_db_config", {}) or {}),
        )
        print("✅ Storage manager initialized")
        return storage_manager
    except Exception as e:
        print(f"❌ Storage setup failed: {str(e)}")
        raise Exception(f"Failed to initialize storage manager: {str(e)}")

def initialize_memory_manager(memory_config: dict, storage_manager: Any) -> Any:
    """Initialize memory manager with configuration."""
    try:
        memory_manager = useMemoryManager(
            memory_limit=memory_config.get("memory_limit", 524288),
            eviction_k=memory_config.get("eviction_k", 3),
            storage_manager=storage_manager,
        )
        print("✅ Memory manager initialized")
        return memory_manager
    except Exception as e:
        print(f"❌ Memory setup failed: {str(e)}")
        raise Exception(f"Failed to initialize memory manager: {str(e)}")

def initialize_tool_manager() -> Any:
    """Initialize tool manager."""
    try:
        print("\n[DEBUG] ===== Setting up Tool Manager =====")
        tool_manager = useToolManager()
        print("✅ Tool manager initialized")
        return tool_manager
    except Exception as e:
        error_msg = str(e)
        stack_trace = traceback.format_exc()
        print(f"[ERROR] Tool Manager Setup Failed: {error_msg}")
        print(f"[ERROR] Stack Trace:\n{stack_trace}")
        raise Exception({
            "error": "Failed to initialize tool manager",
            "message": error_msg,
            "traceback": stack_trace
        })

def initialize_scheduler(components: dict, scheduler_config: dict) -> Any:
    """Initialize scheduler with components and configuration."""
    try:
        scheduler = fifo_scheduler(
            llm=components["llms"],   
            memory_manager=components["memory"],
            storage_manager=components["storage"],
            tool_manager=components["tool"],
            log_mode=scheduler_config.get("log_mode", "console"),
            get_llm_syscall=None,
            get_memory_syscall=None,
            get_storage_syscall=None,
            get_tool_syscall=None,
        )
        scheduler.start()
        print("✅ Scheduler initialized and started")
        return scheduler
    except Exception as e:
        print(f"❌ Scheduler setup failed: {str(e)}")
        raise Exception(f"Failed to initialize scheduler: {str(e)}")

def initialize_agent_factory(agent_factory_config: dict) -> dict:
    """Initialize agent factory with configuration."""
    try:
        submit_agent, await_agent_execution = useFactory(
            log_mode=agent_factory_config.get("log_mode", "console"),
            max_workers=agent_factory_config.get("max_workers", 64)
        )
        print("✅ Agent factory initialized")
        return {
            "submit": submit_agent,
            "await": await_agent_execution,
        }
    except Exception as e:
        print(f"❌ Agent factory setup failed: {str(e)}")
        raise Exception(f"Failed to initialize agent factory: {str(e)}")

def initialize_components() -> dict:
    """Initialize all components with proper error handling and dependencies."""
    components = {
        "llms": None,
        "storage": None,
        "memory": None,
        "tool": None,
        "scheduler": None,
        "factory": None
    }
    
    try:
        # Load configurations
        llms_config = config.get_llms_config()
        storage_config = config.get_storage_config()
        memory_config = config.get_memory_config()
        scheduler_config = config.get_scheduler_config()
        agent_factory_config = config.get_agent_factory_config()

        # Initialize components in order of dependency
        components["llms"] = initialize_llm_core(llms_config)
        components["storage"] = initialize_storage_manager(storage_config)
        
        if not components["storage"]:
            raise Exception("Storage manager must be initialized first")
            
        components["memory"] = initialize_memory_manager(memory_config, components["storage"])
        components["tool"] = initialize_tool_manager()

        # Verify required components
        required_components = ["llms", "memory", "storage", "tool"]
        missing_components = [
            comp for comp in required_components if not components[comp]
        ]
        
        if missing_components:
            raise Exception(f"Missing required components: {', '.join(missing_components)}")

        # Initialize scheduler and agent factory
        components["scheduler"] = initialize_scheduler(components, scheduler_config)
        components["factory"] = initialize_agent_factory(agent_factory_config)

        print("✅ All components initialized successfully")
        return components

    except Exception as e:
        print(f"❌ Component initialization failed: {str(e)}")
        raise

# Initialize components when starting up
active_components = initialize_components()

def restart_kernel():
    """Restart kernel service and reload configuration"""
    try:
        # Clean up existing components
        for component in ["llms", "memory", "storage", "tool"]:
            if active_components[component]:
                if hasattr(active_components[component], "cleanup"):
                    active_components[component].cleanup()
                active_components[component] = None
        
        # Initialize new components
        if not initialize_components():
            raise Exception("Failed to initialize components")
            
        print("✅ All components reinitialized successfully")
        
    except Exception as e:
        print(f"❌ Error restarting kernel: {str(e)}")
        print(f"Stack trace: {traceback.format_exc()}")
        raise

@app.post("/core/refresh")
async def refresh_configuration():
    """Refresh all component configurations"""
    try:
        print("Received refresh request")
        config.refresh()
        print("Configuration reloaded")
        restart_kernel()
        print("Kernel restarted")
        return {
            "status": "success", 
            "message": "Configuration refreshed and components reinitialized"
        }
    except Exception as e:
        print(f"Error during refresh: {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to refresh configuration: {str(e)}"
        )

@app.get("/core/status")
async def get_status():
    """Get the status of all core components."""
    return {
        component: "active" if instance else "inactive"
        for component, instance in active_components.items()
    }


@app.post("/agents/submit")
async def submit_agent(config: AgentSubmit):
    """Submit an agent for execution using the agent factory."""
    if "factory" not in active_components or not active_components["factory"]:
        raise HTTPException(status_code=400, detail="Agent factory not initialized")

    try:
        print(f"\n[DEBUG] ===== Agent Submission =====")
        print(f"[DEBUG] Agent ID: {config.agent_id}")
        print(f"[DEBUG] Task: {config.agent_config.get('task', 'No task specified')}")
        
        _submit_agent = active_components["factory"]["submit"]
        execution_id = _submit_agent(
            agent_name=config.agent_id, task_input=config.agent_config["task"]
        )
        
        return {
            "status": "success",
            "execution_id": execution_id,
            "message": f"Agent {config.agent_id} submitted for execution"
        }
    except Exception as e:
        error_msg = str(e)
        stack_trace = traceback.format_exc()
        print(f"[ERROR] Agent submission failed: {error_msg}")
        print(f"[ERROR] Stack Trace:\n{stack_trace}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Failed to submit agent",
                "message": error_msg,
                "traceback": stack_trace
            }
        )


@app.get("/agents/{execution_id}/status")
async def get_agent_status(execution_id: int):
    """Get the status of a submitted agent."""
    if "factory" not in active_components or not active_components["factory"]:
        raise HTTPException(status_code=400, detail="Agent factory not initialized")
    try:
        print(f"\n[DEBUG] ===== Checking Agent Status =====")
        print(f"[DEBUG] Execution ID: {execution_id}")

        await_execution = active_components["factory"]["await"]
        try:
            result = await_execution(int(execution_id))
        except FileNotFoundError as e:
            raise HTTPException(status_code=404, detail=str(e))

        if result is None:
            return {
                "status": "running",
                "message": "Execution in progress",
                "execution_id": execution_id
            }
        return {
            "status": "completed",
            "result": result,
            "execution_id": execution_id
        }
    except HTTPException:
        raise
    except Exception as e:
        error_msg = str(e)
        stack_trace = traceback.format_exc()
        print(f"[ERROR] Failed to get agent status: {error_msg}")
        print(f"[ERROR] Stack Trace:\n{stack_trace}")

        # Convert unhandled errors to HTTP 500
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Failed to get agent status",
                "message": error_msg,
                "traceback": stack_trace
            }
        )

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
        # print(e)
        print(f"Failed to cleanup components: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to cleanup components: {str(e)}"
        )


@app.post("/query")
async def handle_query(request: QueryRequest):
    breakpoint()
    try:
        if request.query_type == "llm":
            query = LLMQuery(
                messages=request.query_data.messages,
                tools=request.query_data.tools,
                action_type=request.query_data.action_type,
                message_return_type=request.query_data.message_return_type,
            )
            return execute_request(request.agent_name, query)
        elif request.query_type == "storage":
            query = StorageQuery(
                params=request.query_data.params,
                operation_type=request.query_data.operation_type
            )
            return execute_request(request.agent_name, query)
        elif request.query_type == "tool":
            query = ToolQuery(
                params=request.query_data.params,
                operation_type=request.query_data.operation_type
            )
            return execute_request(request.agent_name, query)
        elif request.query_type == "memory":
            query = MemoryQuery(
                params=request.query_data.params,
                operation_type=request.query_data.operation_type
            )
            return execute_request(request.agent_name, query)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/core/config/update")
async def update_config(request: Request):
    """Update configuration and API keys"""
    try:
        data = await request.json()
        logger.info(f"Received config update request: {data}")
        
        provider = data.get("provider")
        api_key = data.get("api_key")
        
        if not all([provider, api_key]):
            raise ValueError("Missing required fields: provider, api_key")
        
        # Update configuration
        config.config["api_keys"][provider] = api_key
        config.save_config()
        
        # Try to reinitialize LLM component
        try:
            await refresh_configuration()
            return {"status": "success", "message": "Configuration updated and services restarted"}
        except Exception as e:
            # If restart fails, roll back the configuration
            config.refresh()  # Reload the original configuration
            raise Exception(f"Failed to restart services with new configuration: {str(e)}")
        
    except Exception as e:
        logger.error(f"Config update failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update configuration: {str(e)}"
        )