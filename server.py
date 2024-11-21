from collections import OrderedDict
from fastapi import Depends, FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from aios.hooks.modules.scheduler import useFIFOScheduler
from aios.hooks.modules.agent import useFactory
from aios.hooks.modules.llm import useCore
from aios.hooks.modules.memory import useMemoryManager
from aios.hooks.modules.storage import useStorageManager
from aios.hooks.modules.tool import useToolManager
from aios.hooks.types.agent import AgentSubmitDeclaration
from aios.hooks.types.llm import LLMParams

from aios.hooks.parser import string
from aios.core.schema import CoreSchema
from aios.hooks.types.parser import ParserQuery

from aios.llm_cores.adapter import LLMAdapter

from aios.utils.utils import (
    parse_global_args,
)

import sys

from pyopenagi.manager.manager import AgentManager

from aios.utils.state import useGlobalState
from dotenv import load_dotenv
import atexit

import json
import uvicorn

from pyopenagi.utils.chat_template import LLMQuery

load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


getLLMState, setLLMState, setLLMCallback = useGlobalState()
getFactory, setFactory, setFactoryCallback = useGlobalState()
getManager, setManager, setManagerCallback = useGlobalState()
getMemoryState, setMemoryState, setMemoryCallback = useGlobalState()
getStorageState, setStorageState, setStorageCallback = useGlobalState()
getToolState, setToolState, setToolCallback = useGlobalState()

setManager(AgentManager("https://my.aios.foundation"))

parser = parse_global_args()
args = parser.parse_args()

# check if the llm information was specified in args

try:
    with open("aios_config.json", "r") as f:
        aios_config = json.load(f)

    # print to stderr
    print("Loaded aios_config.json, ignoring args", file=sys.stderr)

    llm_cores = aios_config["llm_cores"][0]
    # only check aios_config.json
    setLLMState(
        useCore(
            llm_name=llm_cores.get("llm_name"),
            max_gpu_memory=llm_cores.get("max_gpu_memory"),
            eval_device=llm_cores.get("eval_device"),
            max_new_tokens=llm_cores.get("max_new_tokens"),
            log_mode="console",
            use_backend=llm_cores.get("use_backend"),
        )
    )
except FileNotFoundError:
    aios_config = {}
    # only check args
    setLLMState(
        useCore(
            llm_name=args.llm_name,
            max_gpu_memory=args.max_gpu_memory,
            eval_device=args.eval_device,
            max_new_tokens=args.max_new_tokens,
            log_mode=args.llm_kernel_log_mode,
            use_backend=args.use_backend,
        )
    )

setStorageState(useStorageManager(root_dir="root"))

setMemoryState(
    useMemoryManager(
        memory_limit=100 * 1024 * 1024, eviction_k=3, storage_manager=getStorageState()
    )
)

setToolState(useToolManager())

startScheduler, stopScheduler = useFIFOScheduler(
    llm=getLLMState(),
    memory_manager=getMemoryState(),
    storage_manager=getStorageState(),
    tool_manager=getToolState(),
    log_mode=args.scheduler_log_mode,
    # get_queue_message=None
    get_llm_syscall=None,
    get_memory_syscall=None,
    get_storage_syscall=None,
    get_tool_syscall=None,
)


submitAgent, awaitAgentExecution = useFactory(
    log_mode=args.agent_log_mode, max_workers=500
)

setFactory({"submit": submitAgent, "execute": awaitAgentExecution})

startScheduler()


@app.post("/set_kernel")
async def set_kernel(req: LLMParams):
    setLLMState(useCore(**req))

class LLMCoreCallParams(BaseModel):
    llm_name: str
    query: LLMQuery

@app.post("/call_llm_core")
async def call_llm_core(req: LLMCoreCallParams):
    llm = LLMAdapter(req.llm_name)
    core = llm.get_model()

    res = core.execute(req.query)

    return {
        'response': res
    }


@app.post("/add_agent")
async def add_agent(
    req: AgentSubmitDeclaration,
    factory: dict = Depends(getFactory),
):
    try:
        submit_agent = factory.get("submit")

        process_id = submit_agent(agent_name=req.agent_name, task_input=req.task_input)

        return {"success": True, "agent": req.agent_name, "pid": process_id}
    except Exception as e:
        return {"success": False, "exception": f"{e}"}


@app.get("/execute_agent")
async def execute_agent(
    pid: int = Query(..., description="The process ID"),
    factory: dict = Depends(getFactory),
):
    try:
        response = factory.get("execute")(pid)

        return {"success": True, "response": response}
    except Exception as e:
        print("Got an exception while executing agent: ", e)
        return {"success": False, "exception": f"{e}"}


@app.post("/agent_parser")
async def parse_query(req: ParserQuery):
    parser_schema = CoreSchema()
    parser_schema.add_field("agent_name", string, "name of agent").add_field(
        "phrase", string, "agent instruction"
    )


@app.get("/get_all_agents")
async def get_all_agents():
    manager: AgentManager = getManager()

    def transform_string(input_string: str):
        return "/".join(input_string.split("/")[:-1])

    agents = manager.list_available_agents()
    print(agents)
    agent_names = []
    seen = OrderedDict()
    for i, a in enumerate(reversed(agents)):
        transformed = transform_string(a.get("agent"))
        if transformed not in seen:
            seen[transformed] = i
        agent_names.append(transformed)

    # Create the final list with unique display names but original IDs
    _ = [{"id": agents[i].get("agent"), "display": name} for name, i in seen.items()]

    return {"agents": _}


def cleanup():
    stopScheduler()


atexit.register(cleanup)

if __name__ == "__main__":
    config = uvicorn.Config(app, hostname="0.0.0.0", port=8000, log_level="critical")
    server = uvicorn.Server(config)
    server.run()
