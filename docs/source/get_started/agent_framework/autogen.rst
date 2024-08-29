Autogen For AIOS
================

Introduction
------------
AutoGen is an open-source programming framework for building AI agents and 
facilitating cooperation among multiple agents to solve tasks. We made it 
so that agent applications developed with Autogen can run on AIOS by adding
just one line of code.

Quick start
-----------
For installation and usage of Autogen, please refer to the `official Autogen documentation <https://microsoft.github.io/autogen/docs/Getting-Started>`_. 

If you want to run an application developed with Autogen on AIOS, please add ``prepare_autogen()``
before you create an autogen agent.

.. code-block:: python

    from pyopenagi.agents.agent_process import AgentProcessFactory
    from aios.sdk.autogen.adapter import prepare_autogen
    from autogen import ConversableAgent

    # prepate autogen for AIOS
    prepare_autogen()

Then create autogen agent. When running on AIOS, you don't need to supply parameter ``llm_config``, 
this parameter configures the llm model that the agent will use.
Because AIOS will controll the llm call, you should replace ``llm_confg`` with
``agent_process_factory``, which controlls the llm call in AIOS.

.. code-block:: python

    # example process_factory
    process_factory = AgentProcessFactory()

    # Create the agent that uses the LLM.
    assistant = ConversableAgent("agent", agent_process_factory=process_factory)

    # Create the agent that represents the user in the conversation.
    user_proxy = UserProxyAgent("user", code_execution_config=False)

    # Let the assistant start the conversation.  It will end when the user types exit.
    assistant.initiate_chat(user_proxy, message="How can I help you today?")

Don't forget to start the scheduler so that AIOS can manage llm call. 
Details and More examples can be found in https://github.com/agiresearch/AIOS/tree/main/scripts/aios-autogen


prepare_autogen()
-----------------

.. automethod:: aios.sdk.autogen.adapter.prepare_autogen
    :noindex: