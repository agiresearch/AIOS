.. _agent_database:

Web UI
==============

You can interact with the web UI through the frontend and the command line.

Here is a curl example:

.. code-block:: bash

    curl -X POST "http://localhost:8000/add_agent" \
        -H "accept: application/json" \
        -d "{ \"agent_name\": \"example/transcribe_agent\", \
              \"task_input\": \"Listen to me for a few seconds then respond to me\" }"   

Then you get a process PID, which you can execute at will:

.. code-block:: bash

    curl -G -d "pid=1234" "http://localhost:8000/execute_agent" 

Note that the latter uses ``x-www-form-urlencoded`` instead of JSON.

You can also list all agents:

.. code-block:: bash

    curl "http://localhost:8000/get_all_agents"
