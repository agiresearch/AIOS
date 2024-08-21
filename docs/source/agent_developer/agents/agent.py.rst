.. _agent.py.rst:

The agent source code
=====================


Here is some example python:

.. code-block:: python

   from ...react_agent import ReactAgent
   class MyAgent(ReactAgent):
       def __init__(self, 
                agent_name,
                task_input,
                agent_process_factory,
                log_mode: str
       ):
           ReactAgent.__init__(agent_name, task_input, agent_process_factory, log_mode)

From here you can decide whether you want automatic workflow generation or manual workflow. In this case, we will first start with manual workflows.

.. code-block:: python
            # add manual workflow to init
            self.workflow_mode = "manual"
   def manual_workflow(self):
        workflow = [    
           {
                "message": "Use my fancy tool in the specialized way",
                "tool_use": [ "my_fancy_tool", "foo", "bar" ],
            },
            {
                "message": "Respond to the user with the desired response",
                "tool_use": [],
            },
        ]

        return workflow


