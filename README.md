# AIOS: LLM Agent Operating System

<a href='https://arxiv.org/abs/2403.16971'><img src='https://img.shields.io/badge/Paper-PDF-red'></a>
<a href='https://arxiv.org/abs/2312.03815'><img src='https://img.shields.io/badge/Paper-PDF-blue'></a>
[![Code License](https://img.shields.io/badge/Code%20License-MIT-green.svg)](https://github.com/agiresearch/AIOS/blob/main/LICENSE)
<a href='https://discord.gg/B2HFxEgTJX'><img src='https://img.shields.io/badge/Community-Discord-8A2BE2'></a>

AIOS, a Large Language Model (LLM) Agent operating system, embeds large language model into Operating Systems (OS) as the brain of the OS, enabling an operating system "with soul" -- an important step towards AGI. AIOS is designed to optimize resource allocation, facilitate context switch across agents, enable concurrent execution of agents, provide tool service for agents, maintain access control for agents, and provide a rich set of toolkits for LLM Agent developers.


## 🏠 Architecture of AIOS
<p align="center">
<img src="images/AIOS-Architecture.png">
</p>

The objective of AIOS is to provide the LLM kernel which will be an abstraction on top of the OS kernel. The kernel intends to facilitate the installation of agents, which are utilities the kernel can interact with in order to perform tasks the user queries. For example, the MathAgent facilitates mathematical computations, such as currency conversion, integral calculus, or even basic algebraic manipulation. The method of installation is intended to be in a manner similar to [apt](https://en.wikipedia.org/wiki/APT_(software)) or [brew](https://brew.sh).

At the present moment, AIOS is a userspace wrapper around the current kernel. However, this is subject to change as outlined in the [Q4 Goals and Objectives](https://github.com/agiresearch/AIOS/issues/127).

## 📰 News
- **[2024-06-20]** 🔥 Function calling for open-sourced LLMs (native huggingface, vllm, ollama) is supported.
- **[2024-05-20]** 🚀 More agents with ChatGPT-based tool calling are added (i.e., MathAgent, RecAgent, TravelAgent, AcademicAgent and CreationAgent), their profiles and workflows can be found in [OpenAGI](https://github.com/agiresearch/OpenAGI).
- **[2024-05-13]** 🛠️ Local models (diffusion models) as tools from HuggingFace are integrated.
- **[2024-05-01]** 🛠️ The agent creation in AIOS is refactored, which can be found in our [OpenAGI](https://github.com/agiresearch/OpenAGI) package.
- **[2024-04-05]** 🛠️ AIOS currently supports external tool callings (google search, wolframalpha, rapid API, etc).
- **[2024-04-02]** 🤝 AIOS [Discord Community](https://discord.gg/B2HFxEgTJX) is up. Welcome to join the community for discussions, brainstorming, development, or just random chats! For how to contribute to AIOS, please see [CONTRIBUTE](https://github.com/agiresearch/AIOS/blob/main/CONTRIBUTE.md).
- **[2024-03-25]** ✈️ Our paper [AIOS: LLM Agent Operating System](https://arxiv.org/abs/2403.16971) is released and AIOS repository is officially launched!
- **[2023-12-06]** 📋 After several months of working, our perspective paper [LLM as OS, Agents as Apps: Envisioning AIOS, Agents and the AIOS-Agent Ecosystem](https://arxiv.org/abs/2312.03815) is officially released.


## ✈️ Getting Started

### Prerequisites
- Python 3.11
- [Anaconda](https://www.anaconda.com/download/success)
- [git](https://git-scm.com/downloads)
- [pip](https://pypi.org/project/pip/)

At the minimum, we recommend a Nvidia GPU with 4 GB of memory or an ARM based Macbook. It should be able to run on machines with inferior hardware, but task completion time will increase greatly. If you notice a large delay in execution, you can try to use an API based model, such as gpt (paid) or gemini (free).

### Installation
**Git clone AIOS**
```bash
git clone https://github.com/agiresearch/AIOS.git
```
Install the required packages using pip
```bash
conda create -n AIOS python=3.11
source activate AIOS
cd AIOS
pip install -r requirements.txt
```

If you don't have an Nvidia GPU, you could also use a venv
```bash
cd AIOS
python -m venv venv
chmod +x venv/bin/activate
. venv/bin/activate
pip install -r requirements.txt
```

### Usage
If you use open-sourced models from huggingface, you need to setup your [Hugging Face token](https://huggingface.co/settings/tokens) and cache directory
```bash
export HUGGING_FACE_HUB_TOKEN=<YOUR READ TOKEN>
export HF_HOME=<YOUR CACHE DIRECTORY>
```
If you use LLM APIs, you need to setup your API key such as [OpenAI API Key](https://platform.openai.com/api-keys), [Gemini API Key](https://aistudio.google.com/app/apikey)
```bash
export OPENAI_API_KEY=<YOUR OPENAI API KEY>
export GEMINI_API_KEY=<YOUR GEMINI API KEY>
```
If you use external API tools in your agents, please refer to the [How to setup external tools](https://github.com/agiresearch/OpenAGI/blob/main/tools.md).

You can also create .env file from the .env.example file, and then use dotenv to load the environment variables using .env file into your application's environment at runtime.

```bash
cp .env.example .env
```

### Documentation
There is a README.md in each directory which provides a brief explanation on what the contents of the directory include.


#### Demonstration Mode
In the demonstration mode, we provide a toy example: we hardcode three agents and allow you to change the parameters. Then you can see the output of each step in running multiple agents
For open-sourced LLMs, you need to setup the name of the LLM you would like to use the max gpu memory, the evaluation device and the maximum length of generated new tokens.
```bash
# For open-sourced LLMs
python main.py --llm_name <llm_name> --max_gpu_memory <max_gpu_memory> --eval_device <eval_device> --max_new_tokens <max_new_tokens>
## Use meta-llama/Meta-Llama-3-8B-Instruct for example
python main.py --llm_name meta-llama/Meta-Llama-3-8B-Instruct --max_gpu_memory '{"0": "48GB"}' --eval_device "cuda:0" --max_new_tokens 256
```
For inference acceleration, you can also use vllm as the backend.
```bash
## Use meta-llama/Meta-Llama-3-8B-Instruct for example
CUDA_VISILE_DEVICES=0,1 python main.py --llm_name meta-llama/Meta-Llama-3-8B-Instruct --use_backend vllm --max_gpu_memory '{"0": "24GB", "1": "24GB"}' --eval_device "cuda:0" --max_new_tokens 256
```
For close-sourced LLMs, you just need to setup the name of the LLM.
```bash
# For close-sourced LLMs
python main.py --llm_name <llm_name>
## Use gpt-4 for example
python main.py --llm_name gpt-4
```
You can use bash script to start the agent execution like this
```bash
bash scripts/run/gpt4.sh
````
You can use an open-source model on an Apple MacBook with Ollama. First, you will need to pull the model. Let's use llama3 as an example:
```bash
ollama pull llama3:8b
ollama pull llama3:8b
```
Then, you can run the Python script with the input parameter to start using AIOS with Llama3 and Ollama on your MacBook:
```bash
python main.py --llm_name ollama/llama3:8b
python main.py --llm_name ollama/llama3:8b
```
#### Interactive Mode
In the deployment mode, the outputs of running agents are stored in files. And in this mode, you are provided with multiple commands to run agents and see resource usage of agents (e.g., `run \<xxxAgent\>: \<YOUR TASK\>`, `print agent`).
Different from the interactive mode, you need to set all the default loggers as file loggers.
```bash
# For open-sourced LLMs
python simulator.py --llm_name <llm_name> --max_gpu_memory <max_gpu_memory> --eval_device <eval_device> --max_new_tokens <max_new_tokens> --scheduler_log_mode file --agent_log_mode file --llm_kernel_log_mode file
## Use meta-llama/Meta-Llama-3-8B-Instruct for example
python simulator.py --llm_name meta-llama/Meta-Llama-3-8B-Instruct --max_gpu_memory '{"0": "24GB"}' --eval_device "cuda:0" --max_new_tokens 256 --scheduler_log_mode file --agent_log_mode file --llm_kernel_log_mode file
```
```bash
# For close-sourced LLMs
python simulator.py --llm_name <llm_name> --scheduler_log_mode file --agent_log_mode file --llm_kernel_log_mode file
## Use gpt-4 for example
python simulator.py --llm_name gpt-4 --scheduler_log_mode file --agent_log_mode file --llm_kernel_log_mode file
```
You can use bash script to start the interactive simulation session like this
```bash
bash scripts/interactive/gpt4.sh
````

Example run of simulator.py:
```bash
run MathAgent: Calculate the surface area and volume of a cylinder with a radius of 5 units and height of 10 units using the formulas "2 * pi * r * h + 2 * pi * r2" and "pi * r2 * h".
print agent
```

A `run` command will **not output** to the standard output. Instead, it will create a log file.

#### Evaluation Mode
In the evaluation mode, we draw prompts for each agent from `agent_configs/` and evaluate the performance of the agents by allowing the user to specify which agents should be run.

Additionally, you can evaluate the acceleration performance with or without AIOS by comparing the waiting time and turnaround time.

```bash
python eval.py --llm_name gpt-3.5-turbo --agents MathAgent:1,TravelAgent:1,RecAgent:1,AcademicAgent:1,CreationAgent:1
```
You can use bash script to start the agent execution like this
```bash
bash scripts/eval/gpt4.sh
````
If you want to obtain metrics for either concurrent execution (with AIOS) or sequential execution (without AIOS), you can specify the mode parameter when running the eval.py file."
```bash
python eval.py --llm_name gpt-4 --agents MathAgent:1,TravelAgent:1,RecAgent:1,AcademicAgent:1,CreationAgent:1 --mode concurrent-only
python eval.py --llm_name gpt-4 --agents MathAgent:1,TravelAgent:1,RecAgent:1,AcademicAgent:1,CreationAgent:1 --mode sequential-only
```

You could also run the models locally:
```bash
python eval.py --llm_name meta-llama/Meta-Llama-3-8B-Instruct --max_gpu_memory '{"0": "24GB"}' --eval_device "cuda:0" --max_new_tokens 256 --agents MathAgent:1,TravelAgent:1 --mode concurrent-only
```

### Supported LLM backbones
- gpt-3.5-turbo, gpt-4, gpt-4o
- gemini-1.0-pro
- ollama
- claude3
- open-sourced LLM from Huggingface

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
AIOS is dedicated to facilitating the development and deployment of LLM agents in a systematic way, collaborators and contributions are always welcome to foster a cohesive, effective and efficient AIOS-Agent ecosystem!

For detailed information on how to contribute, see [CONTRIBUTE](https://github.com/agiresearch/AIOS/blob/main/CONTRIBUTE.md). If you would like to contribute to the codebase, [issues](https://github.com/agiresearch/AIOS/issues) or [pull requests](https://github.com/agiresearch/AIOS/pulls) are always welcome!

## 🌍 AIOS Contributors
[![AIOS contributors](https://contrib.rocks/image?repo=agiresearch/AIOS&max=300)](https://github.com/agiresearch/AIOS/graphs/contributors)


## 🤝 Discord Channel
If you would like to join the community, ask questions, chat with fellows, learn about or propose new features, and participate in future developments, join our [Discord Community](https://discord.gg/B2HFxEgTJX)!

## 📪 Contact

For issues related to AIOS development, we encourage submitting [issues](https://github.com/agiresearch/AIOS/issues), [pull requests](https://github.com/agiresearch/AIOS/pulls), or initiating discussions in the AIOS [Discord Channel](https://discord.gg/B2HFxEgTJX). For other issues please feel free to contact Kai Mei (marknju2018@gmail.com) and Yongfeng Zhang (yongfeng@email.com).

## 🌟 Star History

[![Star History Chart](https://api.star-history.com/svg?repos=agiresearch/AIOS&type=Date)](https://star-history.com/#agiresearch/AIOS&Date)
