import os
import warnings

from dotenv import load_dotenv

from aios.hooks.starter import aios_starter
from aios.utils.utils import parse_global_args
from pyopenagi.agents.experiment.standard.agent import StandardAgent


class StandardAgentImpl(StandardAgent):

    def custom_prompt(self) -> str:
        return "If you think task is finished, output TERMINATE."

    def custom_terminate(self) -> bool:
        return True if "TERMINATE" in self.short_term_memory.last_message()["content"] else False


def main():
    main_id = os.getpid()
    print(f"Main ID is: {main_id}")
    warnings.filterwarnings("ignore")
    parser = parse_global_args()
    args = parser.parse_args()
    load_dotenv()

    with aios_starter(**vars(args)):
        agent = StandardAgentImpl(
            agent_name="Agent",
            task_input="Write code to solve following problem: In a group of 23 people, the probability of at least "
                       "two having the same birthday is greater"
                       "than 50%"
        )

        result = agent.run()
        print(f"Result: {result}")


# python -m scripts.aios-openagi.write_code --llm_name gpt-4o-mini
if __name__ == '__main__':
    main()
