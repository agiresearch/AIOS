# This is a main script that tests the functionality of specific agents.
# It requires no user input.

from aios.utils.utils import (
    parse_global_args,
)

import warnings

from aios.hooks.llm import useFactory, useKernel, useFIFOScheduler

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
    warnings.filterwarnings("ignore")
    parser = parse_global_args()
    args = parser.parse_args()

    llm_name = args.llm_name
    max_gpu_memory = args.max_gpu_memory
    eval_device = args.eval_device
    max_new_tokens = args.max_new_tokens
    scheduler_log_mode = args.scheduler_log_mode
    agent_log_mode = args.agent_log_mode
    llm_kernel_log_mode = args.llm_kernel_log_mode
    use_backend = args.use_backend
    load_dotenv()

    llm = useKernel(
        llm_name=llm_name,
        max_gpu_memory=max_gpu_memory,
        eval_device=eval_device,
        max_new_tokens=max_new_tokens,
        log_mode=llm_kernel_log_mode,
        use_backend=use_backend
    )

    # run agents concurrently for maximum efficiency using a scheduler
    startScheduler, stopScheduler = useFIFOScheduler(
        llm=llm,
        log_mode=scheduler_log_mode,
        get_queue_message=None
    )

    submitAgent, awaitAgentExecution = useFactory(
        log_mode=agent_log_mode,
        max_workers=500
    )

    startScheduler()

    submitAgent(
        agent_name="example/academic_agent",
        task_input="Find recent papers on the impact of social media on mental health in adolescents."
    )

    # submitAgent(
    #     agent_name="example/travel_planner_agent",
    #     task_input="Please plan a trip for me starting from Sarasota to Chicago for 3 days, from March 22nd to March 24th, 2022. The budget for this trip is set at $1,900."
    # )

    # creation_agent = agent_thread_pool.submit(
    #     agent_factory.run_agent,
    #     "example/creation_agent", "Create an Instagram post: Image of a person using a new tech gadget, text highlighting its key features and benefits."
    # )
    # cocktail_mixlogist = agent_thread_pool.submit(
    #     agent_factory.run_agent,
    #     "example/cocktail_mixlogist", "Create a cocktail for a summer garden party. Guests enjoy refreshing, citrusy flavors. Available ingredients include vodka, gin, lime, lemon, mint, and various fruit juices."
    # )
    # cook_therapist = agent_thread_pool.submit(
    #     agent_factory.run_agent,
    #     "example/cook_therapist", "Develop a low-carb, keto-friendly dinner that is flavorful and satisfying."
    # )
    # fashion_stylist = agent_thread_pool.submit(
    #     agent_factory.run_agent,
    #     "example/fashion_stylist", "Design a custom tuxedo for a slender man with a preference for classic styles, incorporating a modern twist such as velvet lapels or a slim-fit cut."
    # )
    # festival_card_designer = agent_thread_pool.submit(
    #     agent_factory.run_agent,
    #     "example/festival_card_designer", "Design a festival card for a vintage-themed music festival targeting young adults, with a square card size."
    # )
    # fitness_trainer = agent_thread_pool.submit(
    #     agent_factory.run_agent,
    #     "example/fitness_trainer", "Create a workout plan for a busy professional aiming to lose 10 pounds in 3 months."
    # )
    # game_agent = agent_thread_pool.submit(
    #     agent_factory.run_agent,
    #     "example/game_agent", "Recommend a relaxing puzzle game for Nintendo Switch, suitable for a casual player."
    # )
    # interior_decorator = agent_thread_pool.submit(
    #     agent_factory.run_agent,
    #     "example/interior_decorator", "I want to transform my small, dark living room into a bright and airy space. I love minimalist Scandinavian design and prefer neutral colors. Can you help me?"
    # )
    # language_tutor = agent_thread_pool.submit(
    #     agent_factory.run_agent,
    #     "example/language_tutor", "Help me improve my English presentation skills by providing tips on structure, delivery, and visual aids."
    # )
    # logo_creator = agent_thread_pool.submit(
    #     agent_factory.run_agent,
    #     "example/logo_creator", "Design a minimalist logo for a tech startup specializing in AI-powered cybersecurity solutions."
    # )
    # math_agent = agent_thread_pool.submit(
    #     agent_factory.run_agent,
    #     "example/math_agent", "Solve the equation: 2^(3x-1) = 5^(x+2)."
    # )
    # meme_creator = agent_thread_pool.submit(
    #     agent_factory.run_agent,
    #     "example/meme_creator", "Create a meme about the struggles of adulting."
    # )
    # music_composer = agent_thread_pool.submit(
    #     agent_factory.run_agent,
    #     "example/music_composer", "Compose a dreamy indie-pop song with a catchy chorus."
    # )
    # plant_care_assistant = agent_thread_pool.submit(
    #     agent_factory.run_agent,
    #     "example/plant_care_assistant", "How can I revive a dying peace lily with brown tips?"
    # )
    # music_composer = agent_thread_pool.submit(
    #     agent_factory.run_agent,
    #     "example/music_composer", "Compose a dreamy indie-pop song with a catchy chorus."
    # )
    # rec_agent = agent_thread_pool.submit(
    #     agent_factory.run_agent,
    #     "example/rec_agent", "Recommend a Wes Anderson-style comedy set in the 1970s about a dysfunctional family."
    # )
    # story_teller = agent_thread_pool.submit(
    #     agent_factory.run_agent,
    #     "example/story_teller", "Create a dystopian short story featuring a protagonist with a unique biological adaptation, exploring themes of societal oppression and rebellion."
    # )
    # tech_support_agent = agent_thread_pool.submit(
    #     agent_factory.run_agent,
    #     "example/tech_support_agent", "My Windows 10 laptop is running extremely slow, even after restarting and closing unnecessary programs. I've noticed high disk usage, but I don't know how to fix it."
    # )
    # travel_agent = agent_thread_pool.submit(
    #     agent_factory.run_agent,
    #     "example/tech_support_agent", "I want to take a trip to Paris, France from July 4th to July 10th, 2024, and I am traveling from New York City. Help me plan this trip."
    # )

    awaitAgentExecution()

    stopScheduler()

    clean_cache(root_directory="./")


if __name__ == "__main__":
    main()
