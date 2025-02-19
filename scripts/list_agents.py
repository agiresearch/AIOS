# This file provides functionality to list both offline and online AIOS agents.
# It can display locally installed agents as well as agents available for installation
# from the AIOS foundation.

import os
import importlib
from pathlib import Path
from typing import Dict, List
from cerebrum.manager.agent import AgentManager
import platformdirs

def parse_version_from_filename(filename: str) -> str:
    """Extract version from a filename like 'agent_1.2.3.agent'

    Args:
        filename (str): The filename to parse version from

    Returns:
        str: The extracted version string
    """
    return filename.replace('agent_', '').replace('.agent', '')

def get_offline_agents() -> Dict[str, List[str]]:
    """Get all locally downloaded/installed agents with their versions

    This function checks multiple locations for installed agents:
    - Cerebrum built-in agents
    - User's cache directory

    Returns:
        Dict[str, List[str]]: A dictionary mapping agent IDs to their available versions
    """
    offline_agents = {}

    # Check in Cerebrum built-in agents
    # try:
    #     cerebrum_path = importlib.util.find_spec('cerebrum').submodule_search_locations[0]
    #     example_paths = [
    #         os.path.join(cerebrum_path, "example", "agents"),
    #         os.path.join(cerebrum_path, "cerebrum", "example", "agents")
    #     ]

    #     for example_path in example_paths:
    #         if os.path.exists(example_path):
    #             for agent in os.listdir(example_path):
    #                 agent_path = os.path.join(example_path, agent)
    #                 if os.path.isdir(agent_path) and os.path.exists(os.path.join(agent_path, 'agent.py')):
    #                     agent_id = f"example/{agent}"
    #                     if agent_id not in offline_agents:
    #                         offline_agents[agent_id] = ["built-in"]
    # except (ImportError, AttributeError):
    #     print("Error getting offline agents: cerebrum package not found")

    # Check in cache directory
    try:
        cache_dir = Path(platformdirs.user_cache_dir("cerebrum"))
        if cache_dir.exists():
            for author in cache_dir.iterdir():
                if author.is_dir():
                    for agent in author.iterdir():
                        if agent.is_dir():
                            agent_id = f"{author.name}/{agent.name}"
                            versions = []
                            for version_file in agent.glob("*.agent"):
                                version = parse_version_from_filename(version_file.stem)
                                versions.append(version)
                            if versions:
                                offline_agents[agent_id] = sorted(versions, key=lambda v: [int(x) for x in v.split('.')])
    except Exception as e:
        print(f"Error getting offline agents: Could not access cache directory: {str(e)}")

    return offline_agents

def get_online_agents() -> Dict[str, List[str]]:
    """Get all available online agents from AIOS foundation with their versions

    This function connects to the AIOS foundation server to retrieve a list of
    all available agents and their versions.

    Returns:
        Dict[str, List[str]]: A dictionary mapping agent IDs to their available versions
    """
    online_agents = {}
    try:
        manager = AgentManager("https://app.aios.foundation/")
        agent_list = manager.list_available_agents()
        for agent_info in agent_list:
            # Parse the full agent path which includes version
            full_path = agent_info["agent"]
            agent_path, version = full_path.rsplit("/", 1)
            if agent_path in online_agents:
                online_agents[agent_path].append(version)
            else:
                online_agents[agent_path] = [version]

        # Sort versions for each agent
        for agent_id in online_agents:
            online_agents[agent_id] = sorted(online_agents[agent_id], key=lambda v: [int(x) for x in v.split('.')])

    except Exception as e:
        print(f"Error getting online agents: {str(e)}")

    return online_agents

def main():
    """Main function to list all offline and online AIOS agents

    This function retrieves and displays:
    - Offline agents that are ready to use (locally installed)
    - Online agents that are available to install
    Each agent entry shows its latest version and any other available versions.
    """
    # Get offline and online agents
    offline_agents = get_offline_agents()
    online_agents = get_online_agents()

    # Print results
    print("\n=== List of Agents ===")

    print("Offline Agents (Ready to Use):")
    print("-" * 50)
    if offline_agents:
        for agent_id in sorted(offline_agents.keys()):
            versions = offline_agents[agent_id]
            if len(versions) == 1 and versions[0] in ["local", "built-in"]:
                print(f"  • {agent_id} [{versions[0]}]")
            else:
                latest_version = versions[-1] if versions else "unknown"
                other_versions = versions[:-1] if len(versions) > 1 else []
                version_str = f"v{latest_version}"
                if other_versions:
                    version_str += f" (also: {', '.join(f'v{v}' for v in other_versions)})"
                print(f"  • {agent_id} [{version_str}]")
    else:
        print("  No agents installed locally")
    print("-" * 50)

    print("\nOnline Agents (Available to Install):")
    print("-" * 50)
    installable_agents = set(online_agents.keys()) - set(offline_agents.keys())
    if installable_agents:
        for agent_id in sorted(installable_agents):
            versions = online_agents[agent_id]
            latest_version = versions[-1] if versions else "unknown"
            other_versions = versions[:-1] if len(versions) > 1 else []
            version_str = f"v{latest_version}"
            if other_versions:
                version_str += f" (also: {', '.join(f'v{v}' for v in other_versions)})"
            print(f"  • {agent_id} [{version_str}]")
    else:
        print("  No additional agents available to install")
    print("-" * 50)

if __name__ == "__main__":
    main()
