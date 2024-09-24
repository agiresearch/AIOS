# This is a main script that tests the functionality of specific agents.
# It requires no user input.

from aios.utils.utils import (
    parse_global_args,
)
import os
import warnings

from aios.hooks.llm import aios_starter

from aios.utils.utils import delete_directories
from dotenv import load_dotenv


def clean_cache(root_directory):
    targets = {
        ".ipynb_checkpoints",
        "__pycache__",
        ".pytest_cache",
        "context_restoration",
    }
    delete_directories(root_directory, targets)


def main():
    # parse arguments and set configuration for this run accordingly
    main_id = os.getpid()
    print(f"Main ID is: {main_id}")
    warnings.filterwarnings("ignore")
    parser = parse_global_args()
    args = parser.parse_args()
    load_dotenv()

    with aios_starter(**vars(args)) as (submit_agent, await_agent_execution):

        # register your agents and submit agent tasks
        """ submitAgent(
            agent_name="example/academic_agent",
            task_input="Find recent papers on the impact of social media on mental health in adolescents."
        )
        """

        """
        submitAgent(
            agent_name="om-raheja/transcribe_agent",
            task_input="listen to my yap for 5 seconds and write a response to it"
        )
        """

        """
        submitAgent(
            agent_name="example/cocktail_mixlogist",
            task_input="Create a cocktail for a summer garden party. Guests enjoy refreshing, citrusy flavors. Available ingredients include vodka, gin, lime, lemon, mint, and various fruit juices."
        )
        """

        """
        submitAgent(
            agent_name="example/cook_therapist",
            task_input="Develop a low-carb, keto-friendly dinner that is flavorful and satisfying."
        )
        """

        agent_tasks = [
            ["example/academic_agent", "Tell me what is the prollm paper mainly about"]
            # ["example/cocktail_mixlogist", "Create a cocktail for a summer garden party. Guests enjoy refreshing, citrusy flavors. Available ingredients include vodka, gin, lime, lemon, mint, and various fruit juices."]
        ]

        agent_ids = []
        for agent_name, task_input in agent_tasks:
            agent_id = submit_agent(
                agent_name=agent_name,
                task_input=task_input
            )
            agent_ids.append(agent_id)

        for agent_id in agent_ids:
            await_agent_execution(agent_id)

    clean_cache(root_directory="./")


if __name__ == "__main__":
    main()
