Use MetaGPT
===========

Introduction
------------
MetaGPT is a multi-agent framework. We made it
so that agent applications developed with MetaGPT can run on AIOS by adding
just one line of code.

Quick start
-----------
For installation and usage of open-interpreter, please refer to the `official metagpt documentation <https://docs.deepwisdom.ai/main/en/>`_.

If you want to run an application developed with MetaGPT on AIOS, please add ``prepare_framework()``
before you use MetaGPT, and select a framework type through ``FrameworkType``. When you want to
use MetaGPT, you should use ``FrameworkType.MetaGPT``.

Then nothing needs to change, use MetaGPT as usual.

.. code-block:: python

        with aios_starter(**vars(args)):
            prepare_framework(FrameworkType.MetaGPT)

            repo: ProjectRepo = generate_repo("Create a 2048 game")  # or ProjectRepo("<path>")
            print(repo)

or use Data Interpreter to write code:

.. code-block:: python

        with aios_starter(**vars(args)):
            prepare_framework(FrameworkType.MetaGPT)

            async def di_main():
                di = DataInterpreter()
                await di.run("Run data analysis on sklearn Iris dataset, include a plot")

            asyncio.run(di_main())  # or await main() in a jupyter notebook setting


``aios_starter`` will start the scheduler so that AIOS can manage llm call.
Details and More examples can be found in https://github.com/agiresearch/AIOS/tree/main/scripts/aios-metagpt

MetaGPT requires a longer output context to generate longer code,
so you may need to use ``--max_new_tokens`` to set a larger output token length.

.. code-block:: shell

    python scripts/aios-metagpt/example_aios_metagpt.py --llm_name gpt-4o-mini --max_new_tokens 4000
