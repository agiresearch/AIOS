import argparse
from typing import List, Tuple

from aios.utils.utils import delete_directories, humanify_agent, parse_global_args
from aios.hooks.llm import useFactory, useKernel, useFIFOScheduler
from pyopenagi.agents.interact import Interactor

from dotenv import load_dotenv
import warnings

def clean_cache(root_directory):
    targets = {
        ".ipynb_checkpoints",
        "__pycache__",
        ".pytest_cache",
        "context_restoration",
    }
    delete_directories(root_directory, targets)

def get_all_agents() -> dict[str, str]:
    interactor = Interactor()
    agents = interactor.list_available_agents()
    agent_names = {}
    for a in agents:
        agent_names[humanify_agent(a["agent"])] = a["agent"]

    return agent_names


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

def get_user_task() -> str:
    return input("Enter the task for the agent: ")

def main():
    warnings.filterwarnings("ignore")
    parser = parse_global_args()
    args = parser.parse_args()


    load_dotenv()

    llm = useKernel(
        llm_name=args.llm_name,
        max_gpu_memory=args.max_gpu_memory,
        eval_device=args.eval_device,
        max_new_tokens=args.max_new_tokens,
        log_mode=args.llm_kernel_log_mode,
        use_backend=args.use_backend
    )

    startScheduler, stopScheduler = useFIFOScheduler(
        llm=llm,
        log_mode=args.scheduler_log_mode,
        get_queue_message=None
    )

    submitAgent, awaitAgentExecution = useFactory(
        log_mode=args.agent_log_mode,
        max_workers=500
    )

    startScheduler()


    print("""
            \033c
            Welcome to the Agent REPL.
            Please select an agent by pressing tab.
            To exit, press Ctrl+C.
          """)

    # check for getch
    getch = None
    try:
        from getch import getch
    except ImportError:
        print("""
The terminal will NOT look pretty without getch. Please install it.
pip install getch
              """)
        getch = input

    # shell loop
    try: 
        while True:
            chosen_agent = ""
            agents = get_all_agents()

            # shell prompt
            print(f"[{args.llm_name}]> ", end="")

            # check if the user put in a tab
            if getch() != "\t":
                continue



            try:
                from pyfzf.pyfzf import FzfPrompt
                fzf = FzfPrompt()

                selected = fzf.prompt(list(agents.keys()))

                if (len(selected) == 0):
                    print("No agent selected. Please try again.")
                    continue
                
                chosen_agent = agents[selected[0]]

            except ImportError:
                print("pyfzf is not installed. Falling back to default reader.")
                display_agents(list(agents.keys()))
                chosen_agent, _ = "example/" + get_user_choice(agents)

            task = get_user_task()

            try:
                agent_id = submitAgent(
                    agent_name=chosen_agent,
                    task_input=task
                )

                awaitAgentExecution(agent_id)
            except Exception as e:
                print(f"An error occurred: {str(e)}")
    except KeyboardInterrupt:
        stopScheduler()
        clean_cache(root_directory="./")

if __name__ == "__main__":
    main()
