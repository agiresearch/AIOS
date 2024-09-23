import os
import json
import re
from pyopenagi.manager.manager import AgentManager

def modify_files(directory):
    manager = AgentManager('http://localhost:3000')

    for root, dirs, files in os.walk(directory):
        if 'agent.py' in files and 'config.json' in files:
            print(f"Processing folder: {root}")
            # Modify agent.py
            agent_path = os.path.join(root, 'agent.py')
            with open(agent_path, 'r') as file:
                content = file.read()
            
            # Replace import statement
            modified_content = re.sub(
                r'from \.\.\.react_agent import ReactAgent',
                'from pyopenagi.agents.react_agent import ReactAgent',
                content
            )
            
            # Find the class name
            class_match = re.search(r'class (\w+)\(ReactAgent\):', modified_content)
            if class_match:
                class_name = class_match.group(1)
            else:
                print(f"Warning: Could not find class name in {agent_path}")
                continue
            
            # Write modified content back to agent.py
            with open(agent_path, 'w') as file:
                file.write(modified_content)
            
            # Modify config.json
            config_path = os.path.join(root, 'config.json')
            with open(config_path, 'r') as file:
                config = json.load(file)
            
            # Add build attribute
            config['build'] = {
                "entry": "agent.py",
                "module": class_name
            }
            
            # Write modified config back to config.json
            with open(config_path, 'w') as file:
                json.dump(config, file, indent=4)
            
            print(f"Modified {agent_path} and {config_path}")

            manager.upload_agent(None, None, None, root)

# Replace this with your actual directory path
directory_path = '/Users/rama2r/AIOS/pyopenagi/agents/example/'

modify_files(directory_path)