# Travel Planner Agent

## Introduction

The Travel Planner Agent is replicated from the RecAgent used in the paper "TravelPlanner: A Benchmark for Real-World Planning with Language Agents".

## Start

This agent depends on the [database](https://drive.google.com/file/d/1pF1Sw6pBmq2sFkJvm-LzJOqrmfWoQgxE/view). Please download it and place it in the `pyopenagi/environments/` directory, then rename the 'database' as 'travelPlanner', like `pyopenagi/environments/travelPlanner`.

Then modify the main() method code in main.py as shown below. This is an example of loop input 5 times. 

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
                        {"query": "Please assist in crafting a travel plan for a solo traveller, journeying from Detroit to San Diego for 3 days, from March 5th to March 7th, 2022. The travel plan should accommodate a total budget of $3,000."},
                        {"query": "Could you devise a travel plan for me? This trip starts in Salt Lake City and ends in San Jose, spanning 3 days from March 4th to March 6th, 2022. The budget for this trip is set at $1,300."},
                        {"query": "Please help create a travel plan starting from Midland and ending in Las Vegas for 1 person. The trip is scheduled from March 5th to March 7th, 2022, and the budget for the trip is set at $1,700."},
                        {"query": "Could you craft a 3-day travel itinerary for me, leaving from Raleigh and going to Tampa, from March 25th to March 27th, 2022, on a budget of $1,000?"}]
    
    agent_tasks = []
    for data in query_data_list:
        agent_task = agent_thread_pool.submit(
            agent_factory.run_agent,
            "example/travel_planner_agent",
            data['query'],
        )
        agent_tasks.append(agent_task)

    res_list = []
    for r in as_completed(agent_tasks):
        _res = r.result()
        res_list.append(_res)

        # write reult to a temporary json file
        with open('temp/travel_planner_result.json', 'w') as json_file:
            json.dump(res_list, json_file, indent=4)

    scheduler.stop()

    clean_cache(root_directory="./")

```

Then run `python main.py --llm_name <your llm name>>`, such as `python main.py --llm_name gpt-4o-mini`

[Others Guide](https://github.com/agiresearch/AIOS)