import subprocess
import os
import time

from _exec import start_server, stop_server

# def run_exec():
#     # Run the _exec.py Python script asynchronously
#     subprocess.Popen(['python', '_exec.py'])

def run_npm():
    # Change directory to the 'web' subdirectory
    os.chdir('web')
    
    # Run npm run dev asynchronously
    subprocess.Popen(['npm', 'run', 'dev'])

if __name__ == "__main__":
    start_server()
    run_npm()
    
    try:
        while True:
            time.sleep(1)
    finally:
        stop_server()