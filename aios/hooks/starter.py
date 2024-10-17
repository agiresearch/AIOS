from contextlib import contextmanager
from typing import Tuple, Callable, Dict, Any
from .modules.llm import useKernel
from .modules.agent import useFactory
from .modules.scheduler import fifo_scheduler


@contextmanager
def aios_starter(
    llm_name: str,
    max_gpu_memory: str,
    eval_device: str,
    max_new_tokens: int,
    scheduler_log_mode: str,
    agent_log_mode: str,
    llm_kernel_log_mode: str,
    use_backend: str,
) -> Tuple[Callable[[str, str], int], Callable[[str], Dict[str, Any]]]:
    """
    Starts a LLM kernel and a scheduler for running agents, returning functions to submit agents and await their execution.

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
        Tuple: A tuple containing the submitAgent and awaitAgentExecution functions.
    """
    llm = useKernel(
        llm_name=llm_name,
        max_gpu_memory=max_gpu_memory,
        eval_device=eval_device,
        max_new_tokens=max_new_tokens,
        log_mode=llm_kernel_log_mode,
        use_backend=use_backend,
    )

    submit_agent, await_agent_execution = useFactory(
        log_mode=agent_log_mode, max_workers=64
    )

    with fifo_scheduler(
        llm=llm,
        log_mode=scheduler_log_mode,
        get_llm_request=None,
        get_memory_request=None,
    ):
        yield submit_agent, await_agent_execution
