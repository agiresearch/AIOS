.. _quickstart:

Quickstart
==========
Be sure to complete the :ref:`installation instructions <aios_installation>` before continuing with this guide.

.. tip::

    For the config of LLM endpoints, multiple API keys may be required to set up.
    Here we provide the .env.example for easier configuration of these API keys,
    you can just copy .env.example as .env and set up the required keys based on your needs.

    .. code-block:: python

        OPENAI_API_KEY=''
        GEMINI_API_KEY=''
        HF_HOME=''
        HF_AUTH_TOKENS=''


Use with OpenAI API
-------------------
You need to get your OpenAI API key from https://platform.openai.com/api-keys.
Then set up your OpenAI API key as an environment variable

.. code-block:: console

    $ export OPENAI_API_KEY=<YOUR_OPENAI_API_KEY>

Then run main.py with the models provided by OpenAI API

.. code-block:: console

    $ python main.py --llm_name gpt-3.5-turbo # use gpt-3.5-turbo for example


Use with Gemini API
-------------------
You need to get your Gemini API key from https://ai.google.dev/gemini-api

.. code-block:: console

    $ export GEMINI_API_KEY=<YOUR_GEMINI_API_KEY>

Then run main.py with the models provided by OpenAI API

.. code-block:: console

    $ python main.py --llm_name gemini-1.5-flash # use gemini-1.5-flash for example

If you want to use open-sourced models provided by huggingface, here we provide three options:
* Use with ollama
* Use with vllm
* Use with native huggingface models

Use with ollama
---------------
You need to download ollama from from https://ollama.com/.

Then you need to start the ollama server either from ollama app

or using the following command in the terminal

.. code-block:: console

    $ ollama serve

To use models provided by ollama, you need to pull the available models from https://ollama.com/library

.. code-block:: console

    $ ollama pull llama3:8b # use llama3:8b for example

ollama can support CPU-only environment, so if you do not have CUDA environment

You can run aios with ollama models by

.. code-block:: console

    $ python main.py --llm_name ollama/llama3:8b --use_backend ollama # use ollama/llama3:8b for example

However, if you have the GPU environment, you can also pass GPU-related parameters to speed up
using the following command

.. code-block:: console

    $ python main.py --llm_name ollama/llama3:8b --use_backend ollama --max_gpu_memory '{"0": "24GB"}' --eval_device "cuda:0" --max_new_tokens 256

Use with native huggingface llm models
--------------------------------------
Some of the huggingface models require authentification, if you want to use all of
the models you need to set up  your authentification token in https://huggingface.co/settings/tokens
and set up it as an environment variable using the following command

.. code-block:: console

    $ export HF_AUTH_TOKENS=<YOUR_TOKEN_ID>


You can run with the

.. code-block:: console

    $ python main.py --llm_name meta-llama/Meta-Llama-3-8B-Instruct --max_gpu_memory '{"0": "24GB"}' --eval_device "cuda:0" --max_new_tokens 256

By default, huggingface will download the models in the `~/.cache` directory.
If you want to designate the download directory, you can set up it using the following command

.. code-block:: console

    $ export HF_HOME=<YOUR_HF_HOME>

Use with vllm
-------------
If you want to speed up the inference of huggingface models, you can use vllm as the backend.

.. note::

    It is important to note that vllm currently only supports linux and GPU-enabled environment.
    So if you do not have the environment, you need to choose other options.

Considering that vllm itself does not support passing designated GPU ids, you need to either
setup the environment variable,

.. code-block:: console

    $ export CUDA_VISIBLE_DEVICES="0" # replace with your designated gpu ids

Then run the command

.. code-block:: console

    $ python main.py --llm_name meta-llama/Meta-Llama-3-8B-Instruct --use_backend vllm --max_gpu_memory '{"0": "24GB"}' --eval_device "cuda:0" --max_new_tokens 256

or you can pass the `CUDA_VISIBLE_DEVICES` as the prefix

.. code-block:: console

    $ CUDA_VISIBLE_DEVICES=0 python main.py --llm_name meta-llama/Meta-Llama-3-8B-Instruct --use_backend vllm --max_gpu_memory '{"0": "24GB"}' --eval_device "cuda:0" --max_new_tokens 256
