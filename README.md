# AIOS: LLM Agent Operating System

<a href='https://arxiv.org/abs/2403.16971'><img src='https://img.shields.io/badge/Paper-PDF-red'></a>
<a href='https://arxiv.org/abs/2312.03815'><img src='https://img.shields.io/badge/Paper-PDF-blue'></a>
[![Code License](https://img.shields.io/badge/Code%20License-MIT-green.svg)](https://github.com/agiresearch/AIOS/blob/main/LICENSE)
<a href='https://discord.gg/B2HFxEgTJX'><img src='https://img.shields.io/badge/Community-Discord-8A2BE2'></a>

<a href="https://trendshift.io/repositories/8908" target="_blank"><img src="https://trendshift.io/api/badge/repositories/8908" alt="agiresearch%2FAIOS | Trendshift" style="width: 250px; height: 55px;" width="250" height="55"/></a>

The goal of AIOS is to build a large language model (LLM) agent operating system, which intends to embed large language model into the operating system as the brain of the OS. AIOS is designed to address problems (e.g., scheduling, context switch, memory management, etc.) during the development and deployment of LLM-based agents, for a better ecosystem among agent developers and users.

## 🏠 Architecture of AIOS
<p align="center">
<img src="images/AIOS-Architecture.png">
</p>

AIOS provides the LLM kernel as an abstraction on top of the OS kernel. The kernel facilitates the installation, execution and usage of agents. Furthermore, the AIOS SDK facilitates the development and deployment of agents.

## 📰 News
- **[2024-07-10]** 🛠️ AIOS documentation template is up: [Code](https://github.com/agiresearch/AIOS/tree/main/docs) and [Website](https://aios.readthedocs.io/en/latest/).
- **[2024-07-03]** 🛠️ AIOS Github issue template is now available [template](https://github.com/agiresearch/AIOS/issues/new/choose).
- **[2024-06-20]** 🔥 Function calling for open-sourced LLMs (native huggingface, vllm, ollama) is supported.
- **[2024-05-20]** 🚀 More agents with ChatGPT-based tool calling are added (i.e., MathAgent, RecAgent, TravelAgent, AcademicAgent and CreationAgent), their profiles and workflows can be found in [OpenAGI](https://github.com/agiresearch/OpenAGI).
- **[2024-05-13]** 🛠️ Local models (diffusion models) as tools from HuggingFace are integrated.
- **[2024-05-01]** 🛠️ The agent creation in AIOS is refactored, which can be found in our [OpenAGI](https://github.com/agiresearch/OpenAGI) package.
- **[2024-04-05]** 🛠️ AIOS currently supports external tool callings (google search, wolframalpha, rapid API, etc).
- **[2024-04-02]** 🤝 AIOS [Discord Community](https://discord.gg/B2HFxEgTJX) is up. Welcome to join the community for discussions, brainstorming, development, or just random chats! For how to contribute to AIOS, please see [CONTRIBUTE](https://github.com/agiresearch/AIOS/blob/main/CONTRIBUTE.md).
- **[2024-03-25]** ✈️ Our paper [AIOS: LLM Agent Operating System](https://arxiv.org/abs/2403.16971) is released and AIOS repository is officially launched!
- **[2023-12-06]** 📋 After several months of working, our perspective paper [LLM as OS, Agents as Apps: Envisioning AIOS, Agents and the AIOS-Agent Ecosystem](https://arxiv.org/abs/2312.03815) is officially released.


## ✈️ Getting Started
Please see our ongoing [documentation](https://aios.readthedocs.io/en/latest/) for more information.
- [Installation](https://aios.readthedocs.io/en/latest/get_started/installation.html)
- [Quickstart](https://aios.readthedocs.io/en/latest/get_started/quickstart.html)

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
