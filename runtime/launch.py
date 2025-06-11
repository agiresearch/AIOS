from typing_extensions import Literal
from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel, model_validator
from typing import Optional, Dict, Any, Union
from dotenv import load_dotenv
import traceback
import json
import logging
import yaml
import os
from datetime import datetime
from pathlib import Path

from aios.hooks.modules.llm import useCore
from aios.hooks.modules.memory import useMemoryManager
from aios.hooks.modules.storage import useStorageManager
from aios.hooks.modules.tool import useToolManager
from aios.hooks.modules.agent import useFactory
from aios.hooks.modules.scheduler import fifo_scheduler_nonblock as fifo_scheduler
from aios.hooks.modules.scheduler import rr_scheduler_nonblock as rr_scheduler

from aios.syscall.syscall import useSysCall
from aios.config.config_manager import config

from cerebrum.llm.apis import LLMQuery, LLMResponse

from cerebrum.memory.apis import MemoryQuery, MemoryResponse

from cerebrum.tool.apis import ToolQuery, ToolResponse

from cerebrum.storage.apis import StorageQuery, StorageResponse

from fastapi.middleware.cors import CORSMiddleware

import asyncio

import uvicorn

import copy

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
global active_components 
active_components = {
    "llm": None,
    "storage": None,
    "memory": None,
    "tool": None
}

global selected_llms
selected_llms = {
    "llms": []
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

    @model_validator(mode='before')
    def convert_query_data(cls, data: Any) -> Any:
        if isinstance(data, dict):
            query_type = data.get('query_type')
            query_data = data.get('query_data')

            if not query_type or not query_data:
                return data

            type_mapping = {
                'llm': LLMQuery,
                'tool': ToolQuery,
                'storage': StorageQuery,
                'memory': MemoryQuery
            }

            target_type = type_mapping.get(query_type)
            if target_type and isinstance(query_data, dict) and not isinstance(query_data, target_type):
                try:
                    data['query_data'] = target_type(**query_data)
                except Exception as e:
                    # Handle potential validation errors if needed
                    # For now, just pass the original data
                    pass
        return data

def initialize_llm_cores(config: dict) -> Any:
    """Initialize LLM core with configuration."""
    try:
        llm_configs = config.get("models", [])
        if not llm_configs:
            raise ValueError("No LLM models configured")
            
        log_mode = config.get("log_mode", "console")
        use_context_manager = config.get("use_context_manager", False)
        # model = models[0]  # Currently using first model as default
        
        llms = useCore(
            llm_configs=llm_configs,
            log_mode=log_mode,
            use_context_manager=use_context_manager
        )
        
        if llms:
            print("✅ LLM cores initialized")
            return llms
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
            log_mode=memory_config.get("log_mode", "console"),
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
        # Get use_context setting from llms config
        llms_config = config.get_llms_config()
        use_context = llms_config.get("use_context_manager", False)

        # Check if trying to use FIFO scheduler with context management
        # if use_context and isinstance(scheduler_config.get("scheduler_type"), str) and scheduler_config.get("scheduler_type").lower() == "fifo":
        #     raise ValueError("FIFO scheduler cannot be used with context management enabled. Please either disable context management or use Round Robin scheduler.")

        # Round Robin scheduler
        if use_context:
            scheduler = rr_scheduler(
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
        else:
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
        components["llms"] = initialize_llm_cores(llms_config)
        components["storage"] = initialize_storage_manager(storage_config)
        
        if not components["storage"]:
            raise Exception("Storage manager must be initialized first")
        print(memory_config)
        components["memory"] = initialize_memory_manager(memory_config, components["storage"])
        print("memory manager: ", components["memory"])
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
        # for component in ["llms", "memory", "storage", "tool"]:
        #     if active_components[component]:
        #         if hasattr(active_components[component], "cleanup"):
        #             active_components[component].cleanup()
        #         active_components[component] = None
        
        # Initialize new components
        active_components = initialize_components()
        if not active_components:
            raise Exception("Failed to initialize components")
            
        print("✅ All components reinitialized successfully")
        
    except Exception as e:
        print(f"❌ Error restarting kernel: {str(e)}")
        print(f"Stack trace: {traceback.format_exc()}")
        raise

@app.get("/status")
async def get_server_status():
    """Check if the server is running and core components are initialized."""
    inactive_components = [
        component for component, instance in active_components.items() if not instance
    ]
    
    if not inactive_components:
        return {"status": "ok", "message": "All core components are active."}
    else:
        return {
            "status": "warning",
            "message": f"Server is running, but some components are inactive: {', '.join(inactive_components)}",
            "inactive_components": inactive_components
        }



@app.post("/user/select/llms")
async def select_llm(request: Request):
    """Select the LLM to use"""
    data = await request.json()
    logger.info(f"Received select LLM request: {data}")

    if data:
        selected_llms["llms"] = copy.deepcopy(data)
        return {"status": "success", "message": f"LLMs {selected_llms['llms']} selected"}
    else:
        return {"status": "warning", "message": "No LLM selected"}

@app.get("/user/selected/llms")
async def check_selected_llms():
    """Check if the LLM is selected"""
    if len(selected_llms["llms"]) > 0:
        return {"status": "success", "message": f"LLM {selected_llms['llms']} selected"}
    else:
        return {"status": "warning", "message": "No LLM selected"}
    
@app.get("/get/mcp/server")
async def get_mcp_server():
    """Get the MCP server"""
    mcp_server_script_path = config.get_mcp_server_script_path()
    if os.path.exists(mcp_server_script_path):
        return {
            "status": "success",
            "path": mcp_server_script_path
        }
    else:
        return {"status": "warning", "message": "MCP server not found"}


@app.post("/core/refresh")
async def refresh_configuration():
    """Refresh all component configurations"""
    try:
        logger.info("Received refresh request")
        config.refresh()
        logger.info("Configuration reloaded")
        restart_kernel()
        logger.info("Kernel restarted")
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


@app.get("/core/llms/check")
async def check_llms():
    """Check if what LLM cores are initialized."""
    return {
        active_components["llms"]
    }

@app.get("/core/llms/list")
async def list_llms():
    """List the names of configured LLMs."""
    if not active_components["llms"]:
        return {
            "status": "warning",
            "message": "LLM core not initialized",
            "llms": []
        }
    try:
        llm_configs = config.get_llms_config().get("models", [])
        
        return {
            "status": "success",
            "llms": llm_configs
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list LLMs: {str(e)}"
        )

# Add new constant for proc directory
PROC_DIR = Path("proc")

# Create proc directory if it doesn't exist
PROC_DIR.mkdir(exist_ok=True)

def save_agent_process_info(agent_id: str, execution_id: int, config: Dict[str, Any]):
    try:
        process_info = {
            "agent_id": agent_id,
            "execution_id": execution_id,
            "status": "running",
            "start_time": datetime.now().isoformat(),
            "config": config,
            "task": config.get("task", "No task specified")
        }
        
        proc_file = PROC_DIR / f"{execution_id}.json"
        with open(proc_file, "w") as f:
            json.dump(process_info, f, indent=2)
            
    except Exception as e:
        print(f"Failed to save process info: {str(e)}")
        # Don't raise exception - this is not critical functionality

def update_agent_process_status(execution_id: int, status: str, result: Any = None):
    try:
        proc_file = PROC_DIR / f"{execution_id}.json"
        if not proc_file.exists():
            return
            
        with open(proc_file) as f:
            process_info = json.load(f)
            
        process_info["status"] = status
        if status == "completed":
            process_info["end_time"] = datetime.now().isoformat()
            process_info["result"] = result
            
        with open(proc_file, "w") as f:
            json.dump(process_info, f, indent=2)
            
    except Exception as e:
        print(f"Failed to update process status: {str(e)}")

@app.get("/agents/ps")
async def list_agent_processes():
    """List all agent processes and their status"""
    try:
        processes = []
        for proc_file in PROC_DIR.glob("*.json"):
            try:
                with open(proc_file) as f:
                    process_info = json.load(f)
                processes.append(process_info)
            except Exception as e:
                print(f"Failed to read process file {proc_file}: {str(e)}")
                continue
                
        # Sort by execution ID
        processes.sort(key=lambda x: x["execution_id"])
        
        return {
            "status": "success",
            "processes": processes
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list processes: {str(e)}"
        )

@app.post("/agents/submit")
async def submit_agent(config: AgentSubmit):
    """Submit an agent for execution using the agent factory."""
    # breakpoint()
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
        
        save_agent_process_info(
            agent_id=config.agent_id,
            execution_id=execution_id,
            config=config.agent_config
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
            
        update_agent_process_status(execution_id, "completed", result)
        
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
        if active_components.get("scheduler") and hasattr(active_components["scheduler"], "stop"):
            active_components["scheduler"].stop()
        active_components["scheduler"] = None

        # Updated to call cleanup on tool manager
        if active_components.get("tool") and hasattr(active_components["tool"], "cleanup"):
            active_components["tool"].cleanup()
        active_components["tool"] = None
        
        # Keep other cleanups as they were
        for component in ["memory", "storage", "llms"]:
            if active_components.get(component):
                if hasattr(active_components[component], "cleanup"):
                    active_components[component].cleanup()
                active_components[component] = None

        # for proc_file in PROC_DIR.glob("*.json"):
        #     try:
        #         proc_file.unlink()
        #     except Exception as e:
        #         print(f"Failed to remove process file {proc_file}: {str(e)}")

        return {"status": "success", "message": "All components cleaned up"}
    except Exception as e:
        # print(e)
        print(f"Failed to cleanup components: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to cleanup components: {str(e)}"
        )


@app.post("/query")
async def handle_query(request: QueryRequest):
    try:
        if request.query_type == "llm":
            query_required_llms = request.query_data.llms
            if query_required_llms is None:
                if len(selected_llms["llms"]) > 0:
                    query_required_llms = copy.deepcopy(selected_llms["llms"])
                
            else:
                if len(selected_llms["llms"]) > 0:
                    # Check if selected LLMs contain all required LLMs
                    for required_llm in query_required_llms:
                        if not any(required_llm["name"] == sel["name"] and required_llm["provider"] == sel["provider"] 
                                for sel in selected_llms["llms"]):
                            raise ValueError(f"Required LLM {required_llm['name']} from {required_llm['provider']} is not selected")
                        
            query = LLMQuery(
                llms=query_required_llms,
                messages=request.query_data.messages,
                tools=request.query_data.tools,
                action_type=request.query_data.action_type,
                message_return_type=request.query_data.message_return_type,
            )
            result_dict = await asyncio.to_thread(
                execute_request, # The method to call
                request.agent_name,               # First arg to execute_request
                query                # Second arg to execute_request
            )
            
            return result_dict
        
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
        
        name = data.get("name")
        provider = data.get("provider")
        api_key = data.get("api_key")
        
        if not all([provider, api_key]):
            raise ValueError("Missing required fields: provider, api_key")
        
        # Update API keys section if api_key is provided
        if api_key:
            if "api_keys" not in config.config:
                config.config["api_keys"] = {}
                
            if provider not in config.config["api_keys"]:
                raise ValueError(f"Provider {provider} is not supported")
            
            config.config["api_keys"][provider] = api_key # Use backend name as the key
            
            
        else:
            raise ValueError("Missing required fields: api_key")
        
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

# Add a main function to run the app directly
if __name__ == "__main__":
    # Get server config from config.yaml
    server_config = config.get_server_config()
    host = server_config.get("host", "0.0.0.0")
    port = server_config.get("port", 8000)
    
    # print(f"Starting AIOS server on {host}:{port}")
    uvicorn.run("runtime.launch:app", host=host, port=port, reload=False)