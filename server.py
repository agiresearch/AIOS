from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from aios.hooks.llm import useFIFOScheduler, useFactory, useKernel
from aios.hooks.types.llm import AgentSubmitDeclaration, LLMParams

from pyopenagi.agents.interact import Interactor

from state import useGlobalState
from dotenv import load_dotenv
import atexit

load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


getLLMState, setLLMState, setLLMCallback = useGlobalState()
getFactory, setFactory, setFactoryCallback = useGlobalState()
getInteractor, setInteracter, setInteracterCallback = useGlobalState()

setInteracter(
    Interactor()
)

#initial
setLLMState(
    useKernel(
        llm_name='gpt-4o-mini',
        max_gpu_memory=None,
        eval_device=None,
        max_new_tokens=256,
        log_mode='console',
        use_backend=None
    )
)

startScheduler, stopScheduler = useFIFOScheduler(
    llm=getLLMState(),
    log_mode='console',
    get_queue_message=None
)


submitAgent, awaitAgentExecution = useFactory(
    log_mode='console',
    max_workers=500
)

setFactory({
    'submit': submitAgent,
    'execute': awaitAgentExecution
})

startScheduler()

@app.post("/set_kernel")
async def set_kernel(req: LLMParams):
    setLLMState(
        useKernel(**req)
    )

@app.post("/add_agent")
async def add_agent(
    req: AgentSubmitDeclaration, 
    factory: dict = Depends(getFactory), 
):
    try:
        submit_agent = factory.get('submit')
        submit_agent(
            agent_name=req.agent_name,
            task_input=req.task_input
        )
        
        return {
            'success': True,
            'agent': req.agent_name
        }
    except Exception as e:
        print(e)
        return {
            'success': False
        }

@app.get("/execute_agents")
async def execute_agents(
    factory: dict = Depends(getFactory),
):
    try:
        response  = factory.get('execute')()
        
        return {
            'success': True,
            'response': response
        }
    except Exception:
        return {
            'success': False
        }


@app.get("/get_all_agents")
async def get_all_agents(
    interactor: Interactor = Depends(getInteractor),
):
    def transform_string(input_string: str):
        last_part = input_string.split('/')[-1].replace('_', ' ')
        return ' '.join(word.capitalize() for word in last_part.split())
    
    agents = interactor.list_available_agents()
    agent_names = [transform_string(a.get('agent')) for a in agents]

    _ =[{
        'id': agents[i].get('agent'),
        'display': agent_names[i]
    } for i in range(len(agents))]
    
    return {
        'agents': _
    }

def cleanup():
    stopScheduler()

atexit.register(cleanup)


    