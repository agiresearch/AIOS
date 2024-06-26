# wrapper around bedrock/anthropic.claude-3

import re
from .base_llm import BaseLLMKernel
import time

from pyopenagi.utils.chat_template import Response

class BedrockLLM(BaseLLMKernel):

    def load_llm_and_tokenizer(self) -> None:
        """
        langchain_community is only needed for this use case
        it doesn't need to be required for the entire project, only when
        running this llm
        """
        assert self.llm_name.startswith("bedrock")
        try:
            from langchain_community.chat_models import BedrockChat
            model_id = self.model_name.split("/")[-1]
            self.model = BedrockChat(
                model_id=model_id,
                model_kwargs={
                    'temperature': 0.0
                }
            )
        except ModuleNotFoundError as err:
            raise err
        except ImportError:
            raise ImportError(
                "Could not import langchain_community python package. "
                "Please install it with `pip install langchain_community`."
            )
        return

    def process(self,
                agent_process,
                temperature=0.0) -> None:
        # ensure its the right model
        assert self.model_name.startswith("bedrock") and \
            re.search(r'claude', self.model_name, re.IGNORECASE)


        """ simple wrapper around langchain functions """
        agent_process.set_status("executing")
        agent_process.set_start_time(time.time())
        prompt = agent_process.message.prompt
        from langchain_core.prompts import ChatPromptTemplate
        chat_template = ChatPromptTemplate.from_messages([
            ("user", f"{prompt}")
        ])
        messages = chat_template.format_messages(prompt=prompt)
        self.model.model_kwargs['temperature'] = temperature
        try:
            response = self.model(messages)
            agent_process.set_response(
                Response(
                    response_message=response.content
                )
            )
        except IndexError:
            raise IndexError(f"{self.model_name} can not generate a valid result, please try again")
        agent_process.set_status("done")
        agent_process.set_end_time(time.time())
        return
