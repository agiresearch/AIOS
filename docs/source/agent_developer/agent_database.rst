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

.. literalinclude:: ../../../pyopenagi/agents/interact.py
    :language: python
