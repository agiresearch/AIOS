SeeAct
======

Introduction
------------
SeeAct is a visual agent framework that enables AI agents to understand and interact with web interfaces. It provides capabilities for web navigation, visual understanding, and complex web-based task execution.

.. note::
   The current implementation primarily uses GPT-4O. Other models' support is documented for reference and future use.

Integration with AIOS
-------------------
AIOS provides native support for SeeAct agents through the command-line interface or Python API.

Command Line Usage
~~~~~~~~~~~~~~~~

.. code-block:: bash

    python run_seeact.py --task "Your task description" [options]

Available Options:
    - ``--task``: Task description (required)
    - ``--llm_name``: LLM model name (default: gpt-4o)
    - ``--max_gpu_memory``: Maximum GPU memory to use (default: 0.3)
    - ``--eval_device``: Evaluation device (default: cpu)
    - ``--max_new_tokens``: Maximum new tokens (default: 1024)
    - ``--scheduler_log_mode``: Scheduler log mode (default: info)
    - ``--agent_log_mode``: Agent log mode (default: info)
    - ``--llm_kernel_log_mode``: LLM kernel log mode (default: info)
    - ``--use_backend``: Backend to use (default: aios)

Python API Usage
~~~~~~~~~~~~~~

.. code-block:: python

    from aios.utils import parse_global_args
    from aios.hooks.llm import aios_starter
    import asyncio

    # Configure and run agent
    with aios_starter(
        llm_name='gpt-4o',
        max_gpu_memory=0.3,
        eval_device='cpu',
        max_new_tokens=1024,
        scheduler_log_mode='info',
        agent_log_mode='info',
        llm_kernel_log_mode='info',
        use_backend='aios'
    ) as (submit_agent, await_agent_execution):
        agent_id = submit_agent(
            agent_name="example/seeact_agent",
            task_input="Your task description",
            model="gpt-4o",
            default_website="https://www.google.com/",
            headless=True
        )
        
        result = await_agent_execution(agent_id)
        if asyncio.iscoroutine(result):
            loop = asyncio.get_event_loop()
            result = loop.run_until_complete(result)

Configuration
------------

Required Setup
~~~~~~~~~~~~~
1. Install dependencies:

   .. code-block:: bash

       pip install seeact

2. Set up API key in ``.env``:

   .. code-block:: bash

       OPENAI_API_KEY=your_key_here

Example Tasks
-----------
1. Web Navigation:

   .. code-block:: bash

       python run_seeact.py --task "Go to wikipedia.org and search for artificial intelligence"

2. Visual Understanding:

   .. code-block:: bash

       python run_seeact.py --task "Find and list the prices of MacBook Pro on Apple's website"

Best Practices
------------
1. Always specify tasks clearly and concisely
2. Use headless mode for production environments
3. Handle rate limits appropriately
4. Implement proper error handling
5. Monitor agent execution logs

Limitations
----------
- Requires valid OpenAI API key
- Network connectivity for web interactions
- Some websites may block automated access
- Browser automation limitations

Error Handling
------------
The script includes built-in error handling:

.. code-block:: python

    try:
        with aios_starter(**config) as (submit_agent, await_agent_execution):
            # Agent execution code
    except Exception as e:
        print(f"Error during execution: {e}")
        # Error handling logic

Additional Information
-------------------
For more detailed information about AIOS integration and advanced usage, please refer to:

- `SeeAct Documentation <https://github.com/agiresearch/AIOS/tree/main/docs/source/agent_developer/agent_framework>`_
- `AIOS API Documentation <https://github.com/agiresearch/AIOS>`_