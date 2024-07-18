# Travel Planner Agent

## Introduction

The Travel Planner Agent is replicated from the RecAgent used in the paper "TravelPlanner: A Benchmark for Real-World Planning with Language Agents".

## Start

This agent depends on the [database](https://drive.google.com/file/d/1pF1Sw6pBmq2sFkJvm-LzJOqrmfWoQgxE/view). Please download it and place it in the `pyopenagi/environment/` directory.

然后修改main.py中的main()方法代码如下面所示
```python
def main():
    # parse arguments and set configuration for this run accordingly
    warnings.filterwarnings("ignore")
    parser = parse_global_args()
    args = parser.parse_args()

    llm_name = args.llm_name
    max_gpu_memory = args.max_gpu_memory
    eval_device = args.eval_device
    max_new_tokens = args.max_new_tokens
    scheduler_log_mode = args.scheduler_log_mode
    agent_log_mode = args.agent_log_mode
    llm_kernel_log_mode = args.llm_kernel_log_mode
    use_backend = args.use_backend
    load_dotenv()

    llm = llms.LLMKernel(
        llm_name=llm_name,
        max_gpu_memory=max_gpu_memory,
        eval_device=eval_device,
        max_new_tokens=max_new_tokens,
        log_mode=llm_kernel_log_mode,
        use_backend=use_backend
    )

    # run agents concurrently for maximum efficiency using a scheduler

    scheduler = FIFOScheduler(llm=llm, log_mode=scheduler_log_mode)

    agent_process_factory = AgentProcessFactory()

    agent_factory = AgentFactory(
        agent_process_queue=scheduler.agent_process_queue,
        agent_process_factory=agent_process_factory,
        agent_log_mode=agent_log_mode,
    )

    agent_thread_pool = ThreadPoolExecutor(max_workers=500)

    scheduler.start()

    query_data_list = [{"query": "Please plan a trip for me starting from Sarasota to Chicago for 3 days, from March 22nd to March 24th, 2022. The budget for this trip is set at $1,900."},
                        {"query": "Please assist in crafting a travel plan for a solo traveller, journeying from Detroit to San Diego for 3 days, from March 5th to March 7th, 2022. The travel plan should accommodate a total budget of $3,000."}]
    
    travel_planner_agent = agent_thread_pool.submit(
        agent_factory.run_agent,
        "example/travel_planner_agent",
        query_data_list[1]['query'],
    )

    agent_tasks = [travel_planner_agent]

    for r in as_completed(agent_tasks):
        _res = r.result()

    scheduler.stop()

    clean_cache(root_directory="./")

```

Then run `python main.py --llm_name <your llm name>>`, such as `python main.py --llm_name gpt-3.5-turbo`

[Others Guide](https://github.com/agiresearch/AIOS)