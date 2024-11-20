import subprocess
import os
import time

import webbrowser

import sys

sys.path.append(os.getcwd())

import uvicorn
import threading
import asyncio
import logging
from server import app

server = None

sys.path.append((os.path.dirname(os.path.abspath(__file__))))

logging.getLogger("uvicorn.error").disabled = True
logging.getLogger("uvicorn.access").disabled = True

def start_server():
    global server
    config = uvicorn.Config(app, host="0.0.0.0", port=8000, log_level="critical")
    server = uvicorn.Server(config)
    thread = threading.Thread(target=server.run)
    thread.start()
    print("Server started")

def stop_server():
    global server
    if server:
        server.should_exit = True
        server.force_exit = True
        try:
            asyncio.run(server.shutdown())
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(server.shutdown())
            loop.close()
        except asyncio.CancelledError:
            pass
        print("Server stopped")
    else:
        print("Server is not running")

def run_npm(open: bool=False):
    # Change directory to the 'web' subdirectory
    os.chdir('agenthub')
    
    # Run npm run dev asynchronously
    if "node_modules" not in os.listdir():
        install_process = subprocess.Popen(['npm', 'install'])
        install_process.wait()
    
    subprocess.Popen(['npm', 'run', 'dev'])

    if open:
        time.sleep(5)
        webbrowser.open_new_tab("http://localhost:3000")


if __name__ == "__main__":
    start_server()
    run_npm(True)

    try:
        while True:
            time.sleep(1)
    finally:
        stop_server()