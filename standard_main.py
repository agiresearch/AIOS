import os
from aios.hooks.llm import aios_starter
from aios.utils.utils import parse_global_args


def main(**kargs):
    main_id = os.getpid()
    print(f"Main ID is: {main_id}")

    with aios_starter(**kargs) as (submit_agent, await_agent_execution):

        agent_tasks = [
            ["experiment/standard", "Where is China?"]
        ]

        agent_ids = []
        for agent_name, task_input in agent_tasks:
            agent_id = submit_agent(agent_name=agent_name, task_input=task_input)
            agent_ids.append(agent_id)

        for agent_id in agent_ids:
            result = await_agent_execution(agent_id)
            print(f"Agent_id: {agent_id} Result: {result}")


if __name__ == '__main__':
    parser = parse_global_args()
    args = parser.parse_args()

    main(**vars(args))
