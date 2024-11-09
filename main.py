# This is a main script that tests the functionality of specific agents.
# It requires no user input.

from aios.utils.utils import (
    parse_global_args,
)
import os
import warnings

from aios.hooks.starter import aios_starter

from aios.utils.utils import delete_directories
from dotenv import load_dotenv
import asyncio

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
        agent_tasks = [
            ["example/academic_agent", "Tell me what is the prollm paper mainly about"],
            [
                "example/seeact_agent",
                "Find the pdf of the paper \"GPT-4V(ision) is a Generalist Web Agent, if Grounded\"",
                {
                    "model": "gpt-4o",  # Using AIOS model
                    "default_website": "https://www.google.com/",
                    "headless": True  # Run browser in headless mode
                }
            ],
            # [
            #     "example/cocktail_mixlogist",
            #     "Create a cocktail for a summer garden party. Guests enjoy refreshing, citrusy flavors. Available ingredients include vodka, gin, lime, lemon, mint, and various fruit juices.",
            # ],
            # [
            #     "example/festival_card_designer",
            #     "Design a festival card for a vintage-themed music festival targeting young adults, with a square card size.",
            # ],
            # [
            #     "example/logo_creator",
            #     "Design a minimalist logo for a tech startup specializing in AI-powered cybersecurity solutions.",
            # ],
            # [
            #     "example/story_teller",
            #     "Create a dystopian short story featuring a protagonist with a unique biological adaptation, exploring themes of societal oppression and rebellion.",
            # ],
            # [
            #     "example/interior_decorator",
            #     "I want to transform my small, dark living room into a bright and airy space. I love minimalist Scandinavian design and prefer neutral colors. Can you help me?",
            # ],
            # ["example/math_agent", "Solve the equation: 2^(3x-1) = 5^(x+2)."],
            # [
            #     "example/cook_therapist",
            #     "Develop a low-carb, keto-friendly dinner that is flavorful and satisfying.",
            # ],
            # ["example/meme_creator", "Create a meme about the struggles of adulting."],
            # [
            #     "example/fitness_trainer",
            #     "Create a workout plan for a busy professional aiming to lose 10 pounds in 3 months.",
            # ],
            # [
            #     "example/music_composer",
            #     "Compose a dreamy indie-pop song with a catchy chorus.",
            # ],
            # [
            #     "example/creation_agent",
            #     "Create an Instagram post: Image of a person using a new tech gadget, text highlighting its key features and benefits.",
            # ],
        ]

        agent_ids = []
        for task in agent_tasks:
            agent_name = task[0]
            task_input = task[1]
            config = task[2] if len(task) > 2 else {}
            
            agent_id = submit_agent(
                agent_name=agent_name,
                task_input=task_input,
                **config
            )
            agent_ids.append(agent_id)

        for agent_id in agent_ids:
            result = await_agent_execution(agent_id)
            if asyncio.iscoroutine(result):
                loop = asyncio.get_event_loop()
                result = loop.run_until_complete(result)

    clean_cache(root_directory="./")

if __name__ == "__main__":
    main()