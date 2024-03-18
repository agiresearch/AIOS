# AIOS: LLM Agent Operating System

<a href='https://github.com/agiresearch/AIOS/blob/main/AIOS.pdf'><img src='https://img.shields.io/badge/Paper-PDF-red'></a> 
[![Code License](https://img.shields.io/badge/Code%20License-MIT-green.svg)](https://github.com/agiresearch/AIOS/blob/main/LICENSE)

AIOS, a Large Language Model (LLM) Agent operating system, embeds large language model into Operating Systems (OS) as the brain of the OS, enabling an operating system "with soul" -- an important step towards AGI. AIOS is designed to optimize resource allocation, facilitate context switch across agents, enable concurrent execution of agents, provide tool service for agents, maintain access control for agents, and provide a rich set of toolkits for LLM Agent developers.


## Architecture of AIOS
<p align="center">
<img src="images/AIOS-Architecture.png">
</p>

## Getting Started

### Installation

**Make sure you have Python >= 3.9**  
Install the required packages using pip  
```bash
pip install -r requirements.txt
```

### Usage
Set up huggingface token and cache directory
```bash
export HUGGING_FACE_HUB_TOKEN=<YOUR READ TOKEN>
export HF_HOME=<YOUR CACHE DIRECTORY>
```
Run the main.py to start
```python
# Use Gemma-2b-it for example
python main.py --llm_name gemma-2b-it
```

