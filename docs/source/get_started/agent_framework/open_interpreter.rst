Open-Interpreter For AIOS
=========================

Introduction
------------
Open Interpreter lets language models run code. We made it
so that agent applications developed with Open Interpreter can run on AIOS by adding
just one line of code.

Quick start
-----------
For installation and usage of open-interpreter, please refer to the `official open-interpreter documentation <https://docs.openinterpreter.com/getting-started/introduction>`_.

If you want to run an application developed with open-interpreter on AIOS, please add ``prepare_interpreter()``
before you use open-interpreter. ``AgentProcessFactory`` is a required parameter.

.. code-block:: python

    from pyopenagi.agents.agent_process import AgentProcessFactory
    from aios.sdk.interpreter.adapter import prepare_interpreter
    from interpreter import interpreter

    # example process_factory
    process_factory = AgentProcessFactory()

    # prepate interpreter for AIOS
    prepare_interpreter(process_factory)

Then nothing needs to change, use interpreter as usual.

.. code-block:: python

    interpreter.chat("In a group of 23 people, the probability of at least two having the same birthday is greater than 50%")


Don't forget to start the scheduler so that AIOS can manage llm call.
Details and More examples can be found in https://github.com/agiresearch/AIOS/tree/main/scripts/aios-interpreter


prepare_interpreter()
---------------------

.. .. automethod:: aios.sdk.interpreter.adapter.prepare_interpreter
..     :noindex:

``prepare_interpreter()``

    Prepare the interpreter for running LLM in aios.

    Parameters:
        **agent_process_factory** - Used to create agent processes.

`Source Code <https://github.com/agiresearch/AIOS/blob/main/aios/sdk/interpreter/adapter.py>`_
