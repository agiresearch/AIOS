import threading
from src.custom_kernels.kernels import GPTKernel
import time
import sys, io


def test_jit_streaming():
    done_event = threading.Event()

    buffer = io.StringIO()
    old_stdout = sys.stdout
    sys.stdout = buffer

    g = GPTKernel()
    
    try:
        g.execute('Write me a 300 word essay on horses please', done_event)

        time.sleep(2) 
        g.pause()
        time.sleep(2)  # Simulate some processing time

        g.play()

        done_event.wait()

    finally:
        # Restore the original stdout
        sys.stdout = old_stdout

    output = buffer.getvalue()
    print(output)  # Print captured output for verification

    assert 'PAUSE' in output, "The word 'PAUSE' was NOT found in the output."
