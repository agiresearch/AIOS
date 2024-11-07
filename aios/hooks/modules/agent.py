from concurrent.futures import ThreadPoolExecutor, Future
from random import randint
from typing import Any, Tuple, Callable, Dict
from aios.hooks.types.agent import AgentSubmitDeclaration, FactoryParams
from aios.hooks.utils.validate import validate
from aios.hooks.stores import queue as QueueStore, processes as ProcessStore

# from aios.hooks.utils import generate_random_string
from pyopenagi.agents.agent_factory import AgentFactory

ids = []

@validate(FactoryParams)
def useFactory(
    params: FactoryParams,
) -> Tuple[Callable[[AgentSubmitDeclaration], int], Callable[[str], Dict[str, Any]]]:
    """
    Initializes the agent factory and returns functions to submit agents and await their execution.

    Args:
        params (FactoryParams): Parameters required to initialize the agent factory.

    Returns:
        Tuple: A tuple containing the submitAgent and awaitAgentExecution functions.
    """
    agent_factory = AgentFactory(
        agent_log_mode=params.log_mode,
    )

    thread_pool = ThreadPoolExecutor(max_workers=params.max_workers)

    @validate(AgentSubmitDeclaration)
    def submitAgent(declaration_params: AgentSubmitDeclaration) -> int:
        """
        Submits an agent for execution and returns a unique process ID.

        Args:
            declaration_params (AgentSubmitDeclaration): Parameters to declare the agent submission.

        Returns:
            int: A unique process ID for the submitted agent.
        """
        _submitted_agent: Future = thread_pool.submit(
            agent_factory.run_agent,
            declaration_params.agent_name,
            declaration_params.task_input,
        )

        # Generate a unique process ID
        random_code = randint(100000, 999999)
        while random_code in ids:
            random_code = randint(100000, 999999)

        ProcessStore.addProcess(_submitted_agent, random_code)

        return random_code

    def awaitAgentExecution(process_id: str) -> Dict[str, Any]:
        """
        Waits for the agent execution to complete and returns the result.

        Args:
            process_id (str): The ID of the process to await.

        Returns:
            dict: The result of the agent execution.

        Raises:
            ValueError: If the process ID is not found.
        """
        future = ProcessStore.AGENT_PROCESSES.get(process_id)

        if future:
            return future.result()
        else:
            raise ValueError(f"Process with ID '{process_id}' not found.")

    return submitAgent, awaitAgentExecution
