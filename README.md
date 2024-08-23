# AIOS: LLM Agent Operating System

<a href='https://arxiv.org/abs/2403.16971'><img src='https://img.shields.io/badge/Paper-PDF-red'></a>
<a href='https://arxiv.org/abs/2312.03815'><img src='https://img.shields.io/badge/Paper-PDF-blue'></a>
<a href='https://aios.readthedocs.io/'><img src='https://img.shields.io/badge/Documentation-AIOS-green'></a>
[![Code License](https://img.shields.io/badge/Code%20License-MIT-orange.svg)](https://github.com/agiresearch/AIOS/blob/main/LICENSE)
<a href='https://discord.gg/B2HFxEgTJX'><img src='https://img.shields.io/badge/Community-Discord-8A2BE2'></a>

<a href="https://trendshift.io/repositories/8908" target="_blank"><img src="https://trendshift.io/api/badge/repositories/8908" alt="agiresearch%2FAIOS | Trendshift" style="width: 250px; height: 55px;" width="250" height="55"/></a>

The goal of AIOS is to build a large language model (LLM) agent operating system, which intends to embed large language model into the operating system as the brain of the OS. AIOS is designed to address problems (e.g., scheduling, context switch, memory management, etc.) during the development and deployment of LLM-based agents, for a better ecosystem among agent developers and users.

## 🏠 Architecture of AIOS
<p align="center">
<img src="images/AIOS-Architecture.png">
</p>

AIOS provides the LLM kernel as an abstraction on top of the OS kernel. The kernel facilitates the installation, execution and usage of agents. Furthermore, the AIOS SDK facilitates the development and deployment of agents.

## 📰 News
- **[2024-07-10]** 📖 AIOS documentation template is up: [Code](https://github.com/agiresearch/AIOS/tree/main/docs) and [Website](https://aios.readthedocs.io/en/latest/).
- **[2024-07-03]** 🛠️ AIOS Github issue template is now available [template](https://github.com/agiresearch/AIOS/issues/new/choose).
- **[2024-06-20]** 🔥 Function calling for open-sourced LLMs (native huggingface, vllm, ollama) is supported.
- **[2024-05-20]** 🚀 More agents with ChatGPT-based tool calling are added (i.e., MathAgent, RecAgent, TravelAgent, AcademicAgent and CreationAgent), their profiles and workflows can be found in [OpenAGI](https://github.com/agiresearch/OpenAGI).
- **[2024-05-13]** 🛠️ Local models (diffusion models) as tools from HuggingFace are integrated.
- **[2024-05-01]** 🛠️ The agent creation in AIOS is refactored, which can be found in our [OpenAGI](https://github.com/agiresearch/OpenAGI) package.
- **[2024-04-05]** 🛠️ AIOS currently supports external tool callings (google search, wolframalpha, rapid API, etc).
- **[2024-04-02]** 🤝 AIOS [Discord Community](https://discord.gg/B2HFxEgTJX) is up. Welcome to join the community for discussions, brainstorming, development, or just random chats! For how to contribute to AIOS, please see [CONTRIBUTE](https://github.com/agiresearch/AIOS/blob/main/CONTRIBUTE.md).
- **[2024-03-25]** ✈️ Our paper [AIOS: LLM Agent Operating System](https://arxiv.org/abs/2403.16971) is released!
- **[2023-12-06]** 📋 After several months of working, our perspective paper [LLM as OS, Agents as Apps: Envisioning AIOS, Agents and the AIOS-Agent Ecosystem](https://arxiv.org/abs/2312.03815) is officially released.


## ✈️ Getting Started
Please see our ongoing [documentation](https://aios.readthedocs.io/en/latest/) for more information.
- [Installation](https://aios.readthedocs.io/en/latest/get_started/installation.html)
- [Quickstart](https://aios.readthedocs.io/en/latest/get_started/quickstart.html)

### Installation

Git clone AIOS
```bash
git clone https://github.com/agiresearch/AIOS.git
```
```bash
cd AIOS
conda create -n venv python=3.10  # For Python 3.10
# or
conda create -n venv python=3.11  # For Python 3.11
conda activate venv
```
or if using pip
```bash
cd AIOS
python -m venv venv
source venv/bin/activate 
cd ..
cd ..
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

Note: `main.py` is deprecated. Please use `exec.py` for the WebUI, or `agent_repl.py` for the TUI.

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
- Supported versions: **Python 3.8 - 3.11**
##### Node
- Supported versions: **LTS** support ONLY

Run
```
python exec.py
```
which should open up `https://localhost:3000` (if it doesn't, navigate to that on your browser)

Interact with all agents by using the `@` to tag an agent.

### Supported LLM Endpoints
- [OpenAI API](https://platform.openai.com/api-keys)
- [Gemini API](https://ai.google.dev/gemini-api)
- [ollama](https://ollama.com/)
- [vllm](https://docs.vllm.ai/en/stable/)
- [native huggingface models (locally)](https://huggingface.co/)

## 🖋️ References
```
@article{mei2024aios,
  title={AIOS: LLM Agent Operating System},
  author={Mei, Kai and Li, Zelong and Xu, Shuyuan and Ye, Ruosong and Ge, Yingqiang and Zhang, Yongfeng}
  journal={arXiv:2403.16971},
  year={2024}
}
@article{ge2023llm,
  title={LLM as OS, Agents as Apps: Envisioning AIOS, Agents and the AIOS-Agent Ecosystem},
  author={Ge, Yingqiang and Ren, Yujie and Hua, Wenyue and Xu, Shuyuan and Tan, Juntao and Zhang, Yongfeng},
  journal={arXiv:2312.03815},
  year={2023}
}
```

## 🚀 Contributions
For how to contribute, see [CONTRIBUTE](https://github.com/agiresearch/AIOS/blob/main/CONTRIBUTE.md). If you would like to contribute to the codebase, [issues](https://github.com/agiresearch/AIOS/issues) or [pull requests](https://github.com/agiresearch/AIOS/pulls) are always welcome!

## 🌍 AIOS Contributors
[![AIOS contributors](https://contrib.rocks/image?repo=agiresearch/AIOS&max=300)](https://github.com/agiresearch/AIOS/graphs/contributors)


## 🤝 Discord Channel
If you would like to join the community, ask questions, chat with fellows, learn about or propose new features, and participate in future developments, join our [Discord Community](https://discord.gg/B2HFxEgTJX)!

## 📪 Contact

For issues related to AIOS development, we encourage submitting [issues](https://github.com/agiresearch/AIOS/issues), [pull requests](https://github.com/agiresearch/AIOS/pulls), or initiating discussions in the AIOS [Discord Channel](https://discord.gg/B2HFxEgTJX). For other issues please feel free to contact Kai Mei (marknju2018@gmail.com) and Yongfeng Zhang (yongfeng@email.com).
