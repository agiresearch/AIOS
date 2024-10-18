.. _agent_index.rst:

Need to know before building agents
===================================

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

Configurations and dependencies
-------------------------------

You are required to include a JSON file with the following attributes:

.. code-block:: json
   
   {
      "name": "name of the agent",
      "description": [
         "description of the agent functionality"
      ],
      "tools": [
         "tool names to be registered"
      ],
      "meta": {
         "author": "",
         "version": "",
         "license": ""
      },
      "build": {
         "entry": "entry file to start the agent",
         "module": "the module name of the agent"
      }
   }

If your agent requires extra libraries (in addition to the AIOS dependent libraries) to run,
you need to put them in the meta_requirements.txt. 

