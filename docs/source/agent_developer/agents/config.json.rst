.. _config.json.rst:

Agent metadata
===================

You are going to include a JSON file with the following attributes:

1. ``name``: Name, spaces separated with _
2. ``description``: An array with one string that contains a description
3. ``tools``: A list of tools used
4. ``meta``: A dictionary with the following keys: ``author``, ``version``, ``license``

For example, here is the config.json for Transcriber Agent:

.. literalinclude:: ../../../../pyopenagi/agents/example/transcribe_agent/config.json
