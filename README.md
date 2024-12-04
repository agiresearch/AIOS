# AIOS: AI Agent Operating System

<a href='https://arxiv.org/abs/2403.16971'><img src='https://img.shields.io/badge/Paper-PDF-red'></a>
<a href='https://arxiv.org/abs/2312.03815'><img src='https://img.shields.io/badge/Paper-PDF-blue'></a>
<a href='https://docs.aios.foundation/'><img src='https://img.shields.io/badge/Documentation-AIOS-green'></a>
[![Code License](https://img.shields.io/badge/Code%20License-MIT-orange.svg)](https://github.com/agiresearch/AIOS/blob/main/LICENSE)
<a href='https://discord.gg/B2HFxEgTJX'><img src='https://img.shields.io/badge/Community-Discord-8A2BE2'></a>
[![Gurubase](https://img.shields.io/badge/Gurubase-Ask%20AIOS%20Guru-006BFF)](https://gurubase.io/g/aios)

<a href="https://trendshift.io/repositories/8908" target="_blank"><img src="https://trendshift.io/api/badge/repositories/8908" alt="agiresearch%2FAIOS | Trendshift" style="width: 250px; height: 55px;" width="250" height="55"/></a>

AIOS is the AI Agent Operating System, which embeds large language model (LLM) into the operating system as the brain of the OS, facilitating the development and deployment of LLM-based AI Agents. AIOS is designed to address problems (e.g., scheduling, context switch, memory management, storage management, tool management, Agent SDK management, etc.) during the development and deployment of LLM-based agents, for a better ecosystem among agent developers and users. AIOS includes the AIOS Kernel (this [AIOS](https://github.com/agiresearch/AIOS) repository) and the AIOS SDK (the [Cerebrum](https://github.com/agiresearch/Cerebrum) repository). AIOS supports both Web UI and Terminal UI.

## 🏠 Architecture of AIOS
### Overview
<p align="center">
<img src="docs/assets/aios-figs/architecture.jpg">
</p>

The AIOS system is comprised of two key components: the AIOS kernel and the AIOS-Agent SDK.
The AIOS kernel acts as an abstraction layer over the operating system kernel, managing various resources that agents require, such as LLM, memory, storage and tool. 
The AIOS-Agent SDK is designed for agent users and developers, enabling them to build and run agent applications by interacting with the AIOS kernel.
AIOS kernel is the current repository and AIOS-Agent SDK can be found at [here](htgithub.com/agiresearch/Cerebrum)

### Modules and Connections
Below shows how agents utilize AIOS-Agent SDK to interact with AIOS kernel and how AIOS kernel receives agent queries and leverage the chain of syscalls that are scheduled and dispatched to run in different modules. 
<p align="center">
<img src="docs/assets/aios-figs/details.png">
</p>

## 📰 News
- **[2024-11-30]** 🔥 AIOS v0.2.0 is released! Including the AIOS Kernel (this [AIOS](https://github.com/agiresearch/AIOS) repository) and the AIOS SDK (The [Cerebrum](https://github.com/agiresearch/Cerebrum) repository).
- **[2024-09-01]** 🔥 AIOS supports multiple agent creation frameworks (e.g., ReAct, Reflexion, OpenAGI, AutoGen, Open Interpreter, MetaGPT). Agents created by these frameworks can onboard AIOS. Onboarding guidelines can be found at the [Doc](https://docs.aios.foundation/aios-docs/aios-agent/how-to-develop-agents).
- **[2024-07-10]** 📖 AIOS documentation is up, which can be found at [Website](https://docs.aios.foundation/).
- **[2024-06-20]** 🔥 Function calling for open-sourced LLMs (native huggingface, vLLM, ollama) is supported.
- **[2024-05-20]** 🚀 More agents with ChatGPT-based tool calling are added (i.e., MathAgent, RecAgent, TravelAgent, AcademicAgent and CreationAgent), their profiles and workflows can be found in [OpenAGI](https://github.com/agiresearch/OpenAGI).
- **[2024-05-13]** 🛠️ Local models (diffusion models) as tools from HuggingFace are integrated.
- **[2024-05-01]** 🛠️ The agent creation in AIOS is refactored, which can be found in our [OpenAGI](https://github.com/agiresearch/OpenAGI) package.
- **[2024-04-05]** 🛠️ AIOS currently supports external tool callings (google search, wolframalpha, rapid API, etc).
- **[2024-04-02]** 🤝 AIOS [Discord Community](https://discord.gg/B2HFxEgTJX) is up. Welcome to join the community for discussions, brainstorming, development, or just random chats! For how to contribute to AIOS, please see [CONTRIBUTE](https://github.com/agiresearch/AIOS/blob/main/docs/CONTRIBUTE.md).
- **[2024-03-25]** ✈️ Our paper [AIOS: LLM Agent Operating System](https://arxiv.org/abs/2403.16971) is released!
- **[2023-12-06]** 📋 After several months of working, our perspective paper [LLM as OS, Agents as Apps: Envisioning AIOS, Agents and the AIOS-Agent Ecosystem](https://arxiv.org/abs/2312.03815) is officially released.


## ✈️ Getting Started
Please see our ongoing [documentation](https://docs.aios.foundation/) for more information.
- [Installation](https://docs.aios.foundation/aios-docs/getting-started/installation)
- [Quickstart](https://docs.aios.foundation/aios-docs/getting-started/quickstart)
- [WebUI Quickstart](https://docs.aios.foundation/aios-docs/getting-started/webui-quickstart)

### Installation
#### Requirements
##### Python
- Supported versions: **Python 3.10 - 3.11**

#### Environment Variables Configuration
AIOS supports several API integrations that require configuration. You can use the following commands to view available API keys:

- `aios env list`: List available API keys
- `aios env set`: List available API keys

Available API keys to configure:
- `OPENAI_API_KEY`: OpenAI API key for accessing OpenAI services
- `GEMINI_API_KEY`: Google Gemini API key for accessing Google's Gemini services
- `HF_HOME`: HuggingFace API token for accessing open-source models

To obtain these API keys:
1. OpenAI API: Visit https://platform.openai.com/api-keys
2. Google Gemini API: Visit https://makersuite.google.com/app/apikey
3. HuggingFace: Visit https://huggingface.co/settings/tokens

#### Installation from source
Git clone AIOS kernel
```bash
git clone https://github.com/agiresearch/AIOS.git
cd AIOS && git checkout v0.2.0.beta
```
Create venv environment (recommended)
```bash
python3.x -m venv venv # Only support for Python 3.10 and 3.11
source venv/bin/activate
```
or create conda environment
```bash
conda create -n venv python=3.x  # Only support for Python 3.10 and 3.11
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
<!-- > [!TIP] -->
>
> For the config of LLM endpoints, multiple API keys may be required to set up.
> Here we provide the .env.example to for easier configuration of these API keys, you can just copy .env.example as .env and set up the required keys based on your needs.

<!-- Note: Please use `launch.py` for the WebUI, or `agent_repl.py` for the TUI. -->
#### Configurations
##### Use with OpenAI API
You need to get your OpenAI API key from https://platform.openai.com/api-keys.
Then set up your OpenAI API key as an environment variable

```bash
export OPENAI_API_KEY=<YOUR_OPENAI_API_KEY>
```

##### Use with Gemini API
You need to get your Gemini API key from https://ai.google.dev/gemini-api

```bash
export GEMINI_API_KEY=<YOUR_GEMINI_API_KEY>
```

If you want to use **open-sourced** models provided by huggingface, here we provide three options:
* Use with ollama
* Use with native huggingface models
* Use with vLLM

##### Use with ollama
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

ollama can support both CPU-only and GPU environment, details of how to use ollama can be found at [here](https://github.com/ollama/ollama)

##### Use with native huggingface llm models
Some of the huggingface models require authentification, if you want to use all of
the models you need to set up  your authentification token in https://huggingface.co/settings/tokens
and set up it as an environment variable using the following command

By default, huggingface will download the models in the `~/.cache` directory.
If you want to designate the download directory, you can set up it using the following command

```bash
export HF_HOME=<YOUR_HF_HOME>
```

##### Use with vLLM
If you want to speed up the inference of huggingface models, you can use vLLM as the backend.

> [!NOTE]
>
> It is important to note that vLLM currently only supports linux and GPU-enabled environment. So if you do not have the environment, you need to choose other options.

Considering that vLLM itself does not support passing designated GPU ids, you need to either
setup the environment variable,

```bash
export CUDA_VISIBLE_DEVICES="0" # replace with your designated gpu ids
```

or you can pass the `CUDA_VISIBLE_DEVICES` as the prefix

#### Launch AIOS
After you setup your keys or environment parameters, then you can follow the instructions below to start.

First, you need to start the AIOS kernel by running the following commands

```
bash runtime/launch_kernel.sh
```

Then you can start the client provided by the AIOS-Agent SDK either in the terminal or in the WebUI. The instructions can be found at [here](https://github.com/agiresearch/Cerebrum)


### Supported Agent Frameworks
- [OpenAGI](https://github.com/agiresearch/openagi)
- [AutoGen](https://github.com/microsoft/autogen)
- [Open-Interpreter](https://github.com/OpenInterpreter/open-interpreter)
- [MetaGPT](https://github.com/geekan/MetaGPT?tab=readme-ov-file)

### Supported LLM Cores
| Provider 🏢 | Model Name 🤖 | Open Source 🔓 | Model String ⌨️ | Backend ⚙️ | Required API Key |
|:------------|:-------------|:---------------|:---------------|:---------------|:----------------|
| Anthropic | Claude 3.5 Sonnet | ❌ | claude-3-5-sonnet-20241022 |anthropic | - |
| Anthropic | Claude 3.5 Haiku | ❌ | claude-3-5-haiku-20241022 |anthropic | - |
| Anthropic | Claude 3 Opus | ❌ | claude-3-opus-20240229 |anthropic | - |
| Anthropic | Claude 3 Sonnet | ❌ | claude-3-sonnet-20240229 |anthropic | - |
| Anthropic | Claude 3 Haiku | ❌ | claude-3-haiku-20240307 |anthropic | - |
| OpenAI | GPT-4 | ❌ | gpt-4 |openai| OPENAI_API_KEY |
| OpenAI | GPT-4 Turbo | ❌ | gpt-4-turbo |openai| OPENAI_API_KEY |
| OpenAI | GPT-4o | ❌ | gpt-4o |openai| OPENAI_API_KEY |
| OpenAI | GPT-4o mini | ❌ | gpt-4o-mini |openai| OPENAI_API_KEY |
| OpenAI | GPT-3.5 Turbo | ❌ | gpt-3.5-turbo |openai| OPENAI_API_KEY |
| Google | Gemini 1.5 Flash | ❌ | gemini-1.5-flash |google| GEMINI_API_KEY |
| Google | Gemini 1.5 Flash-8B | ❌ | gemini-1.5-flash-8b |google| GEMINI_API_KEY |
| Google | Gemini 1.5 Pro | ❌ | gemini-1.5-pro |google| GEMINI_API_KEY |
| Google | Gemini 1.0 Pro | ❌ | gemini-1.0-pro |google| GEMINI_API_KEY |
| Groq | Llama 3.2 90B Vision | ✅ | llama-3.2-90b-vision-preview |groq| - |
| Groq | Llama 3.2 11B Vision | ✅ | llama-3.2-11b-vision-preview |groq| - |
| Groq | Llama 3.1 70B | ✅ | llama-3.1-70b-versatile |groq| - |
| Groq | Llama Guard 3 8B | ✅ | llama-guard-3-8b |groq| - |
| Groq | Llama 3 70B | ✅ | llama3-70b-8192 |groq| - |
| Groq | Llama 3 8B | ✅ | llama3-8b-8192 |groq| - |
| Groq | Mixtral 8x7B | ✅ | mixtral-8x7b-32768 |groq| - |
| Groq | Gemma 7B | ✅ | gemma-7b-it |groq| - |
| Groq | Gemma 2B | ✅ | gemma2-9b-it |groq| - |
| Groq | Llama3 Groq 70B | ✅ | llama3-groq-70b-8192-tool-use-preview |groq| - |
| Groq | Llama3 Groq 8B | ✅ | llama3-groq-8b-8192-tool-use-preview |groq| - |
| ollama | [All Models](https://ollama.com/search) | ✅ | model-name |ollama| - |
| vLLM | [All Models](https://docs.vllm.ai/en/latest/) | ✅ | model-name |vllm| - |
| HuggingFace | [All Models](https://huggingface.co/models/) | ✅ | model-name |huggingface| HF_HOME |

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
For how to contribute, see [CONTRIBUTE](https://github.com/agiresearch/AIOS/blob/main/docs/CONTRIBUTE.md). If you would like to contribute to the codebase, [issues](https://github.com/agiresearch/AIOS/issues) or [pull requests](https://github.com/agiresearch/AIOS/pulls) are always welcome!

## 🌍 AIOS Contributors
[![AIOS contributors](https://contrib.rocks/image?repo=agiresearch/AIOS&max=300)](https://github.com/agiresearch/AIOS/graphs/contributors)


## 🤝 Discord Channel
If you would like to join the community, ask questions, chat with fellows, learn about or propose new features, and participate in future developments, join our [Discord Community](https://discord.gg/B2HFxEgTJX)!
