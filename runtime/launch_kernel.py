from aios.config.config_manager import config
import argparse
import uvicorn
from runtime.kernel import app

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=['start', 'stop', 'restart', 'refresh'])
    args = parser.parse_args()
    
    if args.action == 'start':
        uvicorn.run(app, host="0.0.0.0", port=8000)
    else:
        # Other commands are handled by the aios command line tool
        pass

if __name__ == "__main__":
    main() 