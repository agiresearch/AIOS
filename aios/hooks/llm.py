from concurrent.futures import ThreadPoolExecutor, Future
from contextlib import contextmanager

from typing import Any
from random import randint

from aios.llm_core.llms import LLM

from aios.scheduler.fifo_scheduler import FIFOScheduler

from aios.hooks.types.llm import AgentSubmitDeclaration, FactoryParams, LLMParams, SchedulerParams, LLMRequestQueue, \
    QueueGetMessage, QueueAddMessage, QueueCheckEmpty
from aios.hooks.validate import validate

from aios.hooks.stores import queue as QueueStore, processes as ProcessStore

from aios.hooks.utils import generate_random_string

from pyopenagi.agents.agent_factory import AgentFactory
from pyopenagi.agents.agent_process import AgentProcessFactory

ids = []


@validate(LLMParams)
def useKernel(params: LLMParams) -> LLM:
    return LLM(**params.model_dump())


def useLLMRequestQueue() -> tuple[LLMRequestQueue, QueueGetMessage, QueueAddMessage, QueueCheckEmpty]:
    r_str = generate_random_string()
    _ = LLMRequestQueue()

    QueueStore.LLM_REQUEST_QUEUE[r_str] = _

    def getMessage():
        return QueueStore.getMessage(_)

    def addMessage(message: str):
        return QueueStore.addMessage(_, message)

    def isEmpty():
        return QueueStore.isEmpty(_)

    return _, getMessage, addMessage, isEmpty


@validate(SchedulerParams)
def useFIFOScheduler(params: SchedulerParams):
    if params.get_queue_message is None:
        from aios.hooks.stores._global import global_llm_req_queue_get_message

        params.get_queue_message = global_llm_req_queue_get_message

    scheduler = FIFOScheduler(**params.model_dump())

    def startScheduler():
        scheduler.start()

    def stopScheduler():
        scheduler.stop()

    return startScheduler, stopScheduler


@validate(FactoryParams)
def useFactory(params: FactoryParams):
    process_factory = AgentProcessFactory()

    agent_factory = AgentFactory(
        agent_process_factory=process_factory,
        agent_log_mode=params.log_mode,
    )

    thread_pool = ThreadPoolExecutor(max_workers=params.max_workers)

    @validate(AgentSubmitDeclaration)
    def submitAgent(declaration_params: AgentSubmitDeclaration) -> None:
        _submitted_agent: Future = thread_pool.submit(
            agent_factory.run_agent,
            declaration_params.agent_name,
            declaration_params.task_input
        )
        # _submitted_agent =

        random_code = randint(100000, 999999)

        while random_code in ids:
            random_code = randint(100000, 999999)

        ProcessStore.addProcess(_submitted_agent, random_code)

        return random_code

    # def awaitAgentExecution() -> dict[str, Any]:
    #     res = []

    #     for r in as_completed(ProcessStore.AGENT_PROCESSES):
    #         _ = r.result()
    #         res.append(_)

    #     return res

    def awaitAgentExecution(process_id: str) -> dict[str, Any]:
        future = ProcessStore.AGENT_PROCESSES.get(process_id)

        if future:
            # with threading.Lock():
            # ids = [x for x in ids if x != process_id]
            return future.result()
        else:
            raise ValueError(f"Process with ID '{process_id}' not found.")

    return submitAgent, awaitAgentExecution


@contextmanager
@validate(SchedulerParams)
def fifo_scheduler(params: SchedulerParams):
    """
    A context manager that starts and stops a FIFO scheduler.

    Args:
        params (SchedulerParams): The parameters for the scheduler.
    """
    if params.get_queue_message is None:
        from aios.hooks.stores._global import global_llm_req_queue_get_message
        params.get_queue_message = global_llm_req_queue_get_message

    scheduler = FIFOScheduler(**params.model_dump())

    scheduler.start()
    yield
    scheduler.stop()


@contextmanager
def aios_starter(
    llm_name,
    max_gpu_memory,
    eval_device,
    max_new_tokens,
    scheduler_log_mode,
    agent_log_mode,
    llm_kernel_log_mode,
    use_backend
):
    """
    Starts a LLM kernel and a scheduler for running agents,
    returning a submitAgent and awaitAgentExecution function.

    Args:
        llm_name (str): The name of the LLM kernel to use.
        max_gpu_memory (str): The maximum amount of GPU memory to use.
        eval_device (str): The device to evaluate the LLM on.
        max_new_tokens (int): The maximum number of new tokens to generate.
        scheduler_log_mode (str): The log mode for the scheduler.
        agent_log_mode (str): The log mode for the agents.
        llm_kernel_log_mode (str): The log mode for the LLM kernel.
        use_backend (str): The backend to use for running the LLM kernel.

    Yields:
        submitAgent (Callable[[str, str], str]): A function that submits an agent for execution.
        awaitAgentExecution (Callable[[str], dict[str, Any]]): A function that waits for an agent
         to complete and returns its result.
    """
    llm = useKernel(
        llm_name=llm_name,
        max_gpu_memory=max_gpu_memory,
        eval_device=eval_device,
        max_new_tokens=max_new_tokens,
        log_mode=llm_kernel_log_mode,
        use_backend=use_backend
    )

    # run agents concurrently for maximum efficiency using a scheduler
    submit_agent, await_agent_execution = useFactory(
        log_mode=agent_log_mode,
        max_workers=64
    )

    with fifo_scheduler(llm=llm, log_mode=scheduler_log_mode, get_queue_message=None):
        yield submit_agent, await_agent_execution
