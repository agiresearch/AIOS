from metagpt.software_company import generate_repo, ProjectRepo

from aios.sdk.metagpt.adapter import prepare_metagpt
from experiment.agent.experiment_agent import ExpirementAgent


class MetaGPTAgent(ExpirementAgent):

    def __init__(self):
        prepare_metagpt()

    def run(self, input_str: str):
        repo: ProjectRepo = generate_repo("\nI need you read following details, helping me solving issues by changing "
                                          "code surrounding by '<code> </code>' block. Then write it into a new "
                                          "python file. Result file list should contains a new.py contains the new "
                                          "code''.Details: \n" +
                                          input_str)
        return str(repo)
