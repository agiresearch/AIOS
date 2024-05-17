from src.core_os.agents.config import Agent
from random import randint

    
process_deleter = Agent(name='cpu_deleter', purpose='Ends execution of the program taking up most of the CPU, freeing up its CPU usage', total_usage=float)
system_informer = Agent(name='system_informer', purpose='Gets the current total usage by CPU for all program combined')
system_status = Agent(name='system_status', purpose='Checks if the given value is below the specified CPU usage threshold (threshold is in decimal format, so 45% would be 0.45). True if below, False if above.', value=float, cpu_usage_threshold=float)


def process_deleter_call(total_usage):
    return total_usage - randint(0, 50) / 420.0

def system_informer_call():
    return randint(350, 400) / 420.0

def system_status_call(value, cpu_usage_threshold):
    return float(value) < float(cpu_usage_threshold)

process_deleter._call = process_deleter_call
system_informer._call = system_informer_call
system_status._call = system_status_call
    






    
    

