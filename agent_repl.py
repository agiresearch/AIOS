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


def get_agent_list() -> List[Tuple[str, str]]:
    return [
        ("academic_agent", "Research academic topics"),
        ("travel_planner_agent", "Plan trips and vacations"),
        ("creation_agent", "Create content for social media"),
        ("cocktail_mixologist", "Design cocktails"),
        ("cook_therapist", "Develop recipes and meal plans"),
        ("fashion_stylist", "Design outfits and styles"),
        ("festival_card_designer", "Design festival cards"),
        ("fitness_trainer", "Create workout plans"),
        ("game_agent", "Recommend games"),
        ("interior_decorator", "Design interior spaces"),
        ("language_tutor", "Provide language learning assistance"),
        ("logo_creator", "Design logos"),
        ("math_agent", "Solve mathematical problems"),
        ("meme_creator", "Create memes"),
        ("music_composer", "Compose music"),
        ("plant_care_assistant", "Provide plant care advice"),
        ("rec_agent", "Recommend movies and TV shows"),
        ("story_teller", "Create short stories"),
        ("tech_support_agent", "Provide tech support"),
        ("travel_agent", "Plan travel itineraries")
    ]

def display_agents(agents: List[Tuple[str, str]]):
    print("Available Agents:")
    for i, (name, description) in enumerate(agents, 1):
        print(f"{i}. {name}: {description}")

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


    # try to load pyfzf
    chosen_agent = ""
    try:
        from pyfzf.pyfzf import FzfPrompt
        fzf = FzfPrompt()
        agents = get_all_agents()
        chosen_agent = agents[fzf.prompt(list(agents.keys()))[0]]

    except ImportError:
        print("pyfzf is not installed. Falling back to default reader.")
        agents = get_agent_list()
        display_agents(agents)
        chosen_agent, _ = "example/" + get_user_choice(agents)

    task = get_user_task()
    startScheduler()

    try:
        agent_id = submitAgent(
            agent_name=chosen_agent,
            task_input=task
        )

        awaitAgentExecution(agent_id)
    except Exception as e:
        print(f"An error occurred: {str(e)}")
    finally:
        stopScheduler()

    clean_cache(root_directory="./")

if __name__ == "__main__":
    main()
