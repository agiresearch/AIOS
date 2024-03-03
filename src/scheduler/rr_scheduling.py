from base import BaseScheduler

import queue

import time

def RRScheduler(processes):
    # Initialize a queue for FIFO scheduling
    process_queue = queue.Queue()
    
    # Enqueue all the processes
    for process in processes:
        process_queue.put(process)
    
    # Process the queue
    while not process_queue.empty():
        # Get the next process in line (FIFO)
        current_process = process_queue.get()
        
        # Simulate the process execution
        print(f"Starting {current_process['name']} with duration {current_process['duration']}s")
        time.sleep(current_process['duration'])  # Simulate the time taken to run the process
        print(f"Finished {current_process['name']}\n")

if __name__ == "__main__":
    # Example usage:
    processes = [
        {'name': 'Process A', 'duration': 2},
        {'name': 'Process B', 'duration': 3},
        {'name': 'Process C', 'duration': 1}
    ]
    
    RRScheduler(processes)