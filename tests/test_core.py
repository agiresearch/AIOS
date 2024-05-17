from io import StringIO
import multiprocessing
import sys
import threading

from src.core_os.memory import SessionMemory
from src.core_os.engines import GPTEngine
from src.core_os.step import StepRouter

from src.core_os.agents.cpu_agents import process_deleter, system_informer, system_status

def test_core():
    stdout_buffer = StringIO()
    sys.stdout = stdout_buffer

    memory = SessionMemory()
    router = StepRouter(start=None, pool=set(), agents=[process_deleter, system_informer, system_status], memory=memory)

    engine = GPTEngine()
    outline = engine.query('Task: ```Make sure computer CPU stays under 65% total usage```').get('result')

    router.set_entry(outline[0])

    for step in outline[1:]:
        router.add_step(step)

    router.chain()

    thread = threading.Thread(target=router.execute)
    thread.start()

    thread.join(timeout=15)

    if thread.is_alive():
        output = stdout_buffer.getvalue()
        assert isinstance(output, str)

        router.flag = True
    
