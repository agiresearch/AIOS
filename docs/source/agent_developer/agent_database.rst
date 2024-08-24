.. _agent_database:

Agent Database
==============

Interact with the database to
- List available agents
- Download agent
- Upload agent

Source https://github.com/agiresearch/AIOS/blob/main/pyopenagi/agents/interact.py.

You can download agents with the following command:

.. code-block:: bash

    python3 pyopenagi/agents/interact.py --download author/agent_name

And conversely, upload with a similar command as well:

.. code-block:: bash

    python3 pyopenagi/agents/interact.py --upload author/agent_name

Please note that updating an agent after uploading is not available at this time. When the Agent Hub is finalized, it will be.

The help message for ``interact.py`` is as follows:

.. code-block:: bash

   $ python3 interact.py -h
    usage: interact.py [-h] [--mode {download,upload}] --agent AGENT

    options:
      -h, --help            show this help message and exit
      --mode {download,upload}
      --agent AGENT

