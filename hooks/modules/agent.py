import logging
import traceback
import sys
import json
import os

logger = logging.getLogger(__name__)

def run_agent(agent_name, task_input):
    try:
        logger.debug(f"\n{'='*50}")
        logger.debug(f"Starting agent execution")
        logger.debug(f"Agent name: {agent_name}")
        logger.debug(f"Task input: {task_input}")

        logger.debug(f"{'='*50}\n")
        
        logger.debug("Creating AgentManager instance...")
        manager = AgentManager('https://app.aios.foundation')
        logger.debug("AgentManager instance created successfully")
        
        logger.debug(f"\nAttempting to load agent from path: {agent_name}")
        logger.debug("Calling manager.load_agent with parameters:")
        logger.debug(f"local=True, path={agent_name}")
        
        agent_class, config = manager.load_agent(local=True, path=agent_name)
        
        logger.debug("\nAgent loaded successfully")
        logger.debug(f"Agent class: {agent_class}")
        logger.debug(f"Agent class type: {type(agent_class)}")
        logger.debug(f"Agent config: {json.dumps(config, indent=2)}")
        
    except Exception as e:
        logger.error(f"\n{'='*50}")
        logger.error("Agent execution failed")
        logger.error(f"Error type: {type(e).__name__}")
        logger.error(f"Error message: {str(e)}")
        logger.error(f"Stack trace:\n{traceback.format_exc()}")
        logger.error(f"Current directory: {os.getcwd()}")
        logger.error(f"Python path: {sys.path}")
        logger.error(f"{'='*50}\n")
        
        debug_info = {
            "error": str(e),
            "error_type": type(e).__name__,
            "traceback": traceback.format_exc(),
            "agent_name": agent_name,
            "task_input": task_input,
            "cwd": os.getcwd(),
            "python_path": sys.path
        }
        new_exception = type(e)(f"{str(e)} (Debug info: {json.dumps(debug_info, indent=2)})")
        new_exception.debug_info = debug_info
        raise new_exception from e 