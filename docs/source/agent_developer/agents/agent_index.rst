.. _agent_index.rst:

Develop a new agent
===================

To develop a new agent and run, you need to configure the agent folder strictly as the following format.

.. code-block:: text

   pyopenagi/
   └── agents/
       └── author/
            └── agent_name/
                │── agent.py # source code for your agent
                │── config.json # agent information, e.g., name, usage, license, etc.
                └── meta_requirements.txt # specific dependencies used for running your agent

For example, your author name is 'example', and you have developed an agent called academic_agent used for searching and summarizing articles.
Your local folder will be like the following:

.. code-block:: text

   pyopenagi/
   └── agents/
       └── example/
            └── academic_agent/
                │── agent.py
                │── config.json
                └── meta_requirements.txt


Here is the outline for each file

.. toctree::
   :maxdepth: 2
   :caption: Agent Files

   agent.py
   config.json
   meta_requirements.txt

Here we provide some useful agent templates to use the agent.


.. toctree::
   :maxdepth: 2
   :caption: Agent Templates

   react_agent
