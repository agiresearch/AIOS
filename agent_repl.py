import argparse
from typing import List, Tuple

from fastapi import Depends

from aios.hooks.modules.agent import useFactory
from aios.hooks.modules.llm import useCore
from aios.hooks.modules.scheduler import useFIFOScheduler
from aios.utils.utils import delete_directories, humanify_agent, parse_global_args
from aios.utils.state import useGlobalState

from pyopenagi.agents.interact import Interactor
from pyopenagi.manager.manager import AgentManager

from dotenv import load_dotenv
import warnings

# load the args
warnings.filterwarnings("ignore")
parser = parse_global_args()
parser.add_argument("--no-color")
parser.add_argument("--manager-url", default="https://my.aios.foundation")

args = parser.parse_args()

load_dotenv()

# start the kernel
llm = useCore(
    llm_name=args.llm_name,
    max_gpu_memory=args.max_gpu_memory,
    eval_device=args.eval_device,
    max_new_tokens=args.max_new_tokens,
    log_mode=args.llm_core_log_mode,
    use_backend=args.use_backend,
)

# boilerplate from "launch.py"
# provides an interface for setting state variables
startScheduler, stopScheduler = useFIFOScheduler(
    llm=llm, log_mode=args.scheduler_log_mode, get_queue_message=None
)

submitAgent, awaitAgentExecution = useFactory(
    log_mode=args.agent_log_mode, max_workers=500
)


startScheduler()

getLLMState, setLLMState, setLLMCallback = useGlobalState()
getFactory, setFactory, setFactoryCallback = useGlobalState()
getManager, setManager, setManagerCallback = useGlobalState()

setFactory({"submit": submitAgent, "execute": awaitAgentExecution})

setManager(AgentManager(args.manager_url))

WHITE = "\033[1m"
GREEN = "\033[32m"
BLUE = "\033[34m"
RED = "\033[31m"
YELLOW = "\033[33m"
RESET = "\033[0m"


def clean_cache(root_directory):
    targets = {
        ".ipynb_checkpoints",
        "__pycache__",
        ".pytest_cache",
        "context_restoration",
    }
    delete_directories(root_directory, targets)


def get_all_agents() -> List[str]:
    manager: AgentManager = getManager()

    agents = manager.list_available_agents()

    return [agent["agent"] for agent in agents]


def display_agents(agents: List[str]):
    print("Available Agents:")
    for i, (name) in enumerate(agents, 1):
        print(f"{i}. {name}")


def get_user_choice(agents: List[Tuple[str, str]]) -> Tuple[str, str]:
    while True:
        try:
            choice = int(input("Enter the number of the agent you want to use: "))
            if 1 <= choice <= len(agents):
                return agents[choice - 1]
            else:
                print("Invalid choice. Please try again.")
        except ValueError:
            print("Please enter a valid number.")


def get_user_task(chosen_agent) -> str:
    return input(f"{BLUE}{chosen_agent}:{RESET} ")


def add_agent(
    agent_name: str,
    task_input: str,
):
    try:
        submit_agent = getFactory()["submit"]
        process_id = submit_agent(agent_name=agent_name, task_input=task_input)
        return {"success": True, "agent": agent_name, "pid": process_id}
    except Exception as e:
        return {"success": False, "exception": f"{e}"}


def execute_agent(
    pid: int,
):
    print(getFactory()["execute"])
    response = getFactory()["execute"](pid)
    print(response)
    return {"success": True, "response": response}


print(
    """
        \033c
        Welcome to the Agent REPL.
        Please select an agent by pressing tab.
        To exit, press Ctrl+C.
      """
)

# check for getch
getch = None
try:
    from getch import getch
except ImportError:
    print(
        """
    The terminal will NOT look pretty without getch. Please install it.
    pip install getch
          """
    )
    getch = input

# shell loop
try:
    while True:
        chosen_agent = ""
        agents = get_all_agents()

        # shell prompt
        print(f"{WHITE}[{args.llm_name}]>{RESET} ", end="")

        # check if the user put in a tab
        if getch() != "\t":
            continue

        try:
            from pyfzf.pyfzf import FzfPrompt

            fzf = FzfPrompt()

            selected = fzf.prompt(agents)

            if len(selected) == 0:
                print("No agent selected. Please try again.")
                continue

            chosen_agent = selected[0]

        except ImportError:
            print("pyfzf is not installed. Falling back to default reader.")
            display_agents(list(agents.keys()))
            chosen_agent, _ = "example/" + get_user_choice(agents)

        task = get_user_task(chosen_agent)

        try:
            agent_payload = add_agent(
                agent_name=chosen_agent,
                task_input=task,
            )

            if not agent_payload["success"]:
                print(f"An error occurred: {agent_payload['exception']}")
                continue

            agent_id = agent_payload["pid"]

            print(f"Agent {chosen_agent} started with PID {agent_id}.")

            agent_response = execute_agent(agent_id)

            if not agent_response["success"]:
                print(f"An error occurred: {agent_response['exception']}")
                continue

            print(agent_response["response"])

        except Exception as e:
            print(f"An error occurred: {str(e)}")


except KeyboardInterrupt:
    stopScheduler()
    clean_cache(root_directory="./")
