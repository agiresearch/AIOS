# AIOS: LLM Agent Operating System
The goal of AIOS is to build a large language model (LLM) agent operating system, which intends to embed large language model into the operating system as the brain of the OS. AIOS is designed to address problems (e.g., scheduling, context switch, memory management, etc.) during the development and deployment of LLM-based agents, for a better ecosystem among agent developers and users.

## 🏠 Architecture of AIOS
AIOS provides the LLM kernel as an abstraction on top of the OS kernel. The kernel facilitates the installation, execution and usage of agents. Furthermore, the AIOS SDK facilitates the development and deployment of agents.

## ✈️ Getting Started

### Installation

Git clone AIOS
```bash
git clone https://github.com/agiresearch/AIOS.git
cd AIOS
```
Create venv environment (recommended)
```bash
python -m venv venv
source venv/bin/activate
```
or create conda environment
```bash
conda create -n venv python=3.10  # For Python 3.10
conda create -n venv python=3.11  # For Python 3.11
conda activate venv
```

If you have GPU environments, you can install the dependencies using
```bash
pip install -r requirements-cuda.txt
```
or else you can install the dependencies using
```bash
pip install -r requirements.txt
```

### Quickstart
> [!TIP]
>
> For the config of LLM endpoints, multiple API keys may be required to set up.
> Here we provide the .env.example to for easier configuration of these API keys, you can just copy .env.example as .env and set up the required keys based on your needs.

Note: Please use `launch.py` for the WebUI, or `agent_repl.py` for the TUI.

#### Use with OpenAI API
You need to get your OpenAI API key from https://platform.openai.com/api-keys.
Then set up your OpenAI API key as an environment variable

```bash
export OPENAI_API_KEY=<YOUR_OPENAI_API_KEY>
```

Then run main.py with the models provided by OpenAI API

```python
python main.py --llm_name gpt-3.5-turbo # use gpt-3.5-turbo for example
```

#### Use with Gemini API
You need to get your Gemini API key from https://ai.google.dev/gemini-api

```bash
export GEMINI_API_KEY=<YOUR_GEMINI_API_KEY>
```

Then run main.py with the models provided by OpenAI API

```python
python main.py --llm_name gemini-1.5-flash # use gemini-1.5-flash for example
```

If you want to use **open-sourced** models provided by huggingface, here we provide three options:
* Use with ollama
* Use with native huggingface models
* Use with vllm

#### Use with ollama
You need to download ollama from from https://ollama.com/.

Then you need to start the ollama server either from ollama app

or using the following command in the terminal

```bash
ollama serve
```

To use models provided by ollama, you need to pull the available models from https://ollama.com/library

```bash
ollama pull llama3:8b # use llama3:8b for example
```

ollama can support CPU-only environment, so if you do not have CUDA environment

You can run aios with ollama models by

```python
python main.py --llm_name ollama/llama3:8b --use_backend ollama # use ollama/llama3:8b for example
```

However, if you have the GPU environment, you can also pass GPU-related parameters to speed up
using the following command

```python
python main.py --llm_name ollama/llama3:8b --use_backend ollama --max_gpu_memory '{"0": "24GB"}' --eval_device "cuda:0" --max_new_tokens 256
```

#### Use with native huggingface llm models
Some of the huggingface models require authentification, if you want to use all of
the models you need to set up  your authentification token in https://huggingface.co/settings/tokens
and set up it as an environment variable using the following command

```bash
export HF_AUTH_TOKENS=<YOUR_TOKEN_ID>
```

You can run with the

```python
python main.py --llm_name meta-llama/Meta-Llama-3-8B-Instruct --max_gpu_memory '{"0": "24GB"}' --eval_device "cuda:0" --max_new_tokens 256
```

By default, huggingface will download the models in the `~/.cache` directory.
If you want to designate the download directory, you can set up it using the following command

```bash
export HF_HOME=<YOUR_HF_HOME>
```

#### Use with vllm
If you want to speed up the inference of huggingface models, you can use vllm as the backend.

> [!NOTE]
>
> It is important to note that vllm currently only supports linux and GPU-enabled environment. So if you do not have the environment, you need to choose other options.

Considering that vllm itself does not support passing designated GPU ids, you need to either
setup the environment variable,

```bash
export CUDA_VISIBLE_DEVICES="0" # replace with your designated gpu ids
```

Then run the command

```python
python main.py --llm_name meta-llama/Meta-Llama-3-8B-Instruct --use_backend vllm --max_gpu_memory '{"0": "24GB"}' --eval_device "cuda:0" --max_new_tokens 256
```

or you can pass the `CUDA_VISIBLE_DEVICES` as the prefix

```python
CUDA_VISIBLE_DEVICES=0 python main.py --llm_name meta-llama/Meta-Llama-3-8B-Instruct --use_backend vllm --max_gpu_memory '{"0": "24GB"}' --eval_device "cuda:0" --max_new_tokens 256
```

### Web Quickstart
#### Requirements

##### Python
- Supported versions: **Python 3.9 - 3.11**
##### Node
- Supported versions: **LTS** support ONLY

Run the launch.py to start both the frontend and backend
```
python launch.py
```
which should open up `https://localhost:3000` (if it doesn't, navigate to that on your browser)

Interact with all agents by using the `@` to tag an agent.

### Supported Agent Frameworks
- [OpenAGI](https://github.com/agiresearch/openagi)
- [AutoGen](https://github.com/microsoft/autogen)
- [Open-Interpreter](https://github.com/OpenInterpreter/open-interpreter)
- [MetaGPT](https://github.com/geekan/MetaGPT?tab=readme-ov-file)

### Supported LLM Endpoints
- [OpenAI API](https://platform.openai.com/api-keys)
- [Gemini API](https://ai.google.dev/gemini-api)
- [ollama](https://ollama.com/)
- [vllm](https://docs.vllm.ai/en/stable/)
- [native huggingface models (locally)](https://huggingface.co/)
