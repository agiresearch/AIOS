.. _agent_index.rst:

The standard for developing agents
==================================

To develop a new agent to run on top of the AIOS, you need to follow rules as below.


The structure of agent-related files
------------------------------------

.. code-block:: text

   author/
   └── agent_name/
         │── entry.py # the entry file to run your new agents
         │── config.json # agent information, e.g., name, usage, license, etc.
         └── meta_requirements.txt # specific dependencies used for running your agent

For example, your author name is 'example', and you have developed an agent called academic_agent used for searching and summarizing articles.
Your local folder will be like the following:

.. code-block:: text

   example/
      └── example_agent/
            │── entry.py
            │── config.json
            └── meta_requirements.txt

Configurations in the config.json
---------------------------------

You are required to include a JSON file with the following attributes:

1. ``name``: Name, spaces separated with _
2. ``description``: An array with one string that contains a description
3. ``tools``: A list of tools used
4. ``meta``: A dictionary with the following keys: ``author``, ``version``, ``license``


Dependencies in the meta_requirements.txt
-----------------------------------------

