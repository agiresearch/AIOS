import uvicorn
import threading
import asyncio
import logging
from server import app

server = None

import sys, os
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

if __name__ == "__main__":
    start_server()

    # Example: Stop the server after 10 seconds
    import time
    try:
        while True:
            time.sleep(1)
    except:
        stop_server()
