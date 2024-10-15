Use AutoGen
===========

Introduction
------------
AutoGen is an open-source programming framework for building AI agents and
facilitating cooperation among multiple agents to solve tasks. We made it
so that agent applications developed with Autogen can run on AIOS by adding
just one line of code.

(Only support AutoGen version~0.2 now)

Quick start
-----------
For installation and usage of Autogen, please refer to the `official Autogen documentation <https://microsoft.github.io/autogen/docs/Getting-Started>`_.

If you want to run an application developed with Autogen on AIOS, please add ``prepare_framework()``
before you create an autogen agent, and select a framework type through ``FrameworkType``. When you want to
use AutoGen, you should use ``FrameworkType.AutoGen``.
Then create autogen agent. When running on AIOS, you don't need to supply parameter ``llm_config``,
this parameter configures the llm model that the agent will use.
Because AIOS will deal with the calling of llms in the backend.

.. code-block:: python

        with aios_starter(**vars(args)):

            prepare_framework(FrameworkType.AutoGen)

            # Create the agent that uses the LLM.
            assistant = ConversableAgent("agent")

            # Create the agent that represents the user in the conversation.
            user_proxy = UserProxyAgent("user", code_execution_config=False)

            # Let the assistant start the conversation.  It will end when the user types exit.
            assistant.initiate_chat(user_proxy, message="How can I help you today?")

``aios_starter`` will start the scheduler so that AIOS can manage llm call.
Details and More examples can be found in https://github.com/agiresearch/AIOS/tree/main/scripts/aios-autogen
