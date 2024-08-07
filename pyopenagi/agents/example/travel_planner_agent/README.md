# Travel Planner Agent

## Introduction

The Travel Planner Agent is replicated from the RecAgent used in the paper "TravelPlanner: A Benchmark for Real-World Planning with Language Agents".

## Start

This agent depends on the [database](https://drive.google.com/file/d/1pF1Sw6pBmq2sFkJvm-LzJOqrmfWoQgxE/view). Please download it and place it in the `pyopenagi/environments/` directory, then rename the 'database' as 'travelPlanner', like `pyopenagi/environments/travelPlanner`.

Then submit an agent like:

```python
submitAgent(
        agent_name="example/travel_planner_agent",
        task_input="Please plan a trip for me starting from Sarasota to Chicago for 3 days, from March 22nd to March 24th, 2022. The budget for this trip is set at $1,900."
    )
```

Then run
```python
python main.py --llm_name <your llm name>
```
such as
```python
python main.py --llm_name gpt-4o-mini
```

[Others Guide](https://github.com/agiresearch/AIOS)
