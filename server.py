from fastapi import Depends, FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware

from aios.hooks.llm import useFIFOScheduler, useFactory, useKernel
from aios.hooks.types.llm import AgentSubmitDeclaration, LLMParams

from aios.hooks.parser import string
from aios.core.schema import CoreSchema
from aios.hooks.types.parser import ParserQuery

from aios.utils.utils import (
    parse_global_args,
)

from pyopenagi.manager.manager import AgentManager

from aios.utils.state import useGlobalState
from dotenv import load_dotenv
import atexit

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

setManager(AgentManager('https://agenthub.aios.foundation/'))

# parser = parse_global_args()
# args = parser.parse_args()

# check if the llm information was specified in args

# setLLMState(
#     useKernel(
#         llm_name='gpt-4o-mini',
#         max_gpu_memory=None,
#         eval_device=None,
#         max_new_tokens=256,
#         log_mode='console',
#         use_backend=None
#     )
# )



# deploy specific
# leave commented
# TODO conditional check if in deployment environment
setLLMState(
    useKernel(
        llm_name='mixtral-8x7b-32768',
        max_gpu_memory=None,
        eval_device=None,
        max_new_tokens=512,
        log_mode='console',
        use_backend=None
    )
)


startScheduler, stopScheduler = useFIFOScheduler(
    llm=getLLMState(), log_mode="console", get_queue_message=None
)


submitAgent, awaitAgentExecution = useFactory(log_mode="console", max_workers=500)

setFactory({"submit": submitAgent, "execute": awaitAgentExecution})

startScheduler()


@app.post("/set_kernel")
async def set_kernel(req: LLMParams):
    setLLMState(useKernel(**req))


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
        return '/'.join(
            input_string.split("/")[:-1]
        )

    agents = manager.list_available_agents()
    print(agents)
    agent_names = [transform_string(a.get("agent")) for a in agents]

    _ = [
        {"id": agents[i].get("agent"), "display": agent_names[i]}
        for i in range(len(agents))
    ]

    return {"agents": _}


def cleanup():
    stopScheduler()


atexit.register(cleanup)
