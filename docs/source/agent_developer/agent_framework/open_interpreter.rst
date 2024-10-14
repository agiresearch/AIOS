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
before you use open-interpreter, and select a framework type through ``FrameworkType``. When you want to
use Open-Interpreter, you should use ``FrameworkType.OpenInterpreter``.

Then nothing needs to change, use interpreter as usual.

.. code-block:: python

        with aios_starter(**vars(args)):

            prepare_framework(FrameworkType.OpenInterpreter)

            interpreter.chat("In a group of 23 people, the probability of at least two having the same birthday is greater "
                             "than 50%")

``aios_starter`` will start the scheduler so that AIOS can manage llm call.
Details and More examples can be found in https://github.com/agiresearch/AIOS/tree/main/scripts/aios-interpreter
