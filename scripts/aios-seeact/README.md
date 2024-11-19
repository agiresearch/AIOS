# AIOS-SeeAct Integration

This directory contains scripts for integrating SeeAct with AIOS. SeeAct is a visual agent that can understand and interact with web interfaces.

> **Note**: Current implementation uses GPT-4O for web interaction tasks.

## Setup

### Install Dependencies
```bash
pip install seeact
```

### Set up API Keys
Add your API key in the `.env` file:
```bash
OPENAI_API_KEY=your_key_here  # Required for GPT-4O
```

## Usage

### Basic Usage
```bash
python run_seeact.py --task "Search for pictures of cats on Google Images" --llm_name gpt-4o
```

### Parameters

Required:
- `--task`: The task description for SeeAct agent

Optional:
- `--llm_name`: LLM model name (default: gpt-4o)
- `--max_gpu_memory`: Maximum GPU memory to use (default: 0.3)
- `--eval_device`: Evaluation device (default: cpu)
- `--max_new_tokens`: Maximum new tokens (default: 1024)
- `--scheduler_log_mode`: Scheduler log mode (choices: console, file)
- `--agent_log_mode`: Agent log mode (choices: console, file)
- `--llm_kernel_log_mode`: LLM kernel log mode (choices: console, file)
- `--use_backend`: Backend to use (choices: ollama, vllm)

### Example Tasks

#### Web Navigation:
```bash
python run_seeact.py --task "Find the pdf of the paper GPT-4V(ision) is a Generalist Web Agent, if Grounded" --llm_name gpt-4o
```

## Default Configuration

```python
DEFAULT_SETTINGS = {
    'llm_name': 'gpt-4o',
    'max_gpu_memory': 0.3,
    'eval_device': 'cpu',
    'max_new_tokens': 1024,
    'scheduler_log_mode': 'file',
    'agent_log_mode': 'file',
    'llm_kernel_log_mode': 'file',
    'use_backend': 'aios',
    'headless': True,
    'default_website': 'https://www.google.com/'
}
```

## Implementation Notes
- Uses GPT-4o for web interaction and visual understanding
- Runs in headless mode by default
- Uses Google as the default starting website
- Automated web interaction capabilities

## Limitations
- Requires valid OpenAI API key
- Network connectivity for web interactions
- Some websites may block automated access
- Browser automation limitations
