import subprocess
import os
import time

from _exec import start_server, stop_server
import webbrowser

# def run_exec():
#     # Run the _exec.py Python script asynchronously
#     subprocess.Popen(['python', '_exec.py'])

def run_npm():
    # Change directory to the 'web' subdirectory
    os.chdir('web')
    
    # Run npm run dev asynchronously
    if "node_modules" not in os.listdir():
        install_process = subprocess.Popen(['npm', 'install'])
        install_process.wait()
    
    subprocess.Popen(['npm', 'run', 'dev'])

if __name__ == "__main__":
    start_server()
    run_npm()

    webbrowser.open_new_tab("http://localhost:3000")
    
    try:
        while True:
            time.sleep(1)
    finally:
        stop_server()