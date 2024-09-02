MetaGPT For AIOS
=========================

Introduction
------------
MetaGPT is a multi-agent framework. We made it
so that agent applications developed with MetaGPT can run on AIOS by adding
just one line of code.

Quick start
-----------
For installation and usage of open-interpreter, please refer to the `official metagpt documentation <https://docs.deepwisdom.ai/main/en/>`_.

If you want to run an application developed with MetaGPT on AIOS, please add ``prepare_metagpt()``
before you use MetaGPT. ``AgentProcessFactory`` is a required parameter.

.. code-block:: python

    from pyopenagi.agents.agent_process import AgentProcessFactory
    from aios.sdk.metagpt.adapter import prepare_metagpt

    # example process_factory
    process_factory = AgentProcessFactory()

    # prepate metagpt for AIOS
    prepare_metagpt(process_factory)

Then nothing needs to change, use MetaGPT as usual.

.. code-block:: python

    from metagpt.software_company import generate_repo, ProjectRepo

    repo: ProjectRepo = generate_repo("Create a 2048 game")  # or ProjectRepo("<path>")
    print(repo)  # it will print the repo structure with files

or use Data Interpreter to write code:

.. code-block:: python

    import asyncio
    from metagpt.roles.di.data_interpreter import DataInterpreter

    async def main():
        di = DataInterpreter()
        await di.run("Run data analysis on sklearn Iris dataset, include a plot")

    asyncio.run(main())


Don't forget to start the scheduler so that AIOS can manage llm call.
Details and More examples can be found in https://github.com/agiresearch/AIOS/tree/main/scripts/aios-metagpt


prepare_metagpt()
---------------------

.. automethod:: aios.sdk.metagpt.adapter.prepare_metagpt
    :noindex:
