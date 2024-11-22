import importlib
import os
import json
import base64
import subprocess
import sys
from typing import List, Dict
import requests
from pathlib import Path
import platformdirs
import importlib.util

from cerebrum.manager.package import AgentPackage
from cerebrum.utils.manager import get_newest_version

class AgentManager:
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.base_path = os.path.dirname(os.path.abspath(__file__))
        self.cache_dir = Path(platformdirs.user_cache_dir("cerebrum"))
        self.cache_dir.mkdir(parents=True, exist_ok=True)


    def _version_to_path(self, version: str) -> str:
        return version.replace('.', '-')

    def _path_to_version(self, path_version: str) -> str:
        return path_version.replace('-', '.')

    def package_agent(self, folder_path: str) -> Dict:
        agent_files = self._get_agent_files(folder_path)
        print(folder_path)
        print(agent_files)
        metadata = self._get_agent_metadata(folder_path)

        return {
            "author": metadata.get("meta", {}).get('author'),
            "name": metadata.get('name'),
            "version": metadata.get("meta", {}).get('version'),
            "license": metadata.get("license", "Unknown"),
            "files": agent_files,
            "entry": metadata.get("build", {}).get("entry", "agent.py"),
            "module": metadata.get("build", {}).get("module", "Agent")
        }

    def upload_agent(self, payload: Dict):
        response = requests.post(f"{self.base_url}/cerebrum/upload", json=payload)
        response.raise_for_status()
        print(f"Agent {payload.get('author')}/{payload.get('name')} (v{payload.get('version')}) uploaded successfully.")

    def download_agent(self, author: str, name: str, version: str | None = None) -> tuple[str, str, str]:
        if version is None:
            cached_versions = self._get_cached_versions(author, name)
            version = get_newest_version(cached_versions)

        try:
            cache_path = self._get_cache_path(author, name, version)
        except:
            cache_path = None

        if cache_path is not None and cache_path.exists():
            print(f"Using cached version of {author}/{name} (v{version})")
            return author, name, version

        if version is None:
            params = {
                "author": author,
                "name": name,
            }
        else: 
            params = {
                "author": author,
                "name": name,
                "version": version
            }
        
        response = requests.get(f"{self.base_url}/cerebrum/download", params=params)
        response.raise_for_status()
        agent_data = response.json()

        actual_version = agent_data.get('version', version)
        cache_path = self._get_cache_path(author, name, actual_version)
        print(cache_path)

        self._save_agent_to_cache(agent_data, cache_path)
        print(
            f"Agent {author}/{name} (v{actual_version}) downloaded and cached successfully.")

        if not self.check_reqs_installed(cache_path):
            self.install_agent_reqs(cache_path)

        return author, name, actual_version

    def _get_cached_versions(self, author: str, name: str) -> List[str]:
        agent_dir = self.cache_dir / author / name
        if agent_dir.exists():
            return [self._path_to_version(v.stem) for v in agent_dir.glob("*.agent") if v.is_file()]
        return []

    def _get_cache_path(self, author: str, name: str, version: str) -> Path:
        return self.cache_dir / author / name / f"{self._version_to_path(version)}.agent"

    def _save_agent_to_cache(self, agent_data: Dict, cache_path: Path):
        print(agent_data)
        agent_package = AgentPackage(cache_path)
        agent_package.metadata = {
            "author": agent_data["author"],
            "name": agent_data["name"],
            "version": agent_data["version"],
            "license": agent_data["license"],
            "entry": agent_data["entry"],
            "module": agent_data["module"]
        }
        agent_package.files = {file["path"]: base64.b64decode(file["content"]) for file in agent_data["files"]}
        agent_package.save()

        # Ensure the cache directory exists
        cache_path.parent.mkdir(parents=True, exist_ok=True)

        print(f"Saved agent to cache: {cache_path}")

    def _get_agent_files(self, folder_path: str) -> List[Dict[str, str]]:
        files = []
        for root, _, filenames in os.walk(folder_path):
            for filename in filenames:
                file_path = os.path.join(root, filename)
                relative_path = os.path.relpath(file_path, folder_path)
                with open(file_path, "rb") as f:
                    content = base64.b64encode(f.read()).decode('utf-8')
                files.append({
                    "path": relative_path,
                    "content": content
                })
        return files

    def _get_agent_metadata(self, folder_path: str) -> Dict[str, str]:
        config_path = os.path.join(folder_path, "config.json")
        if os.path.exists(config_path):
            with open(config_path, "r") as f:
                return json.load(f)
        return {}

    def list_available_agents(self) -> List[Dict[str, str]]:
        response = requests.get(f"{self.base_url}/cerebrum/get_all_agents")
        response.raise_for_status()

        response: dict = response.json()

        agent_list = []

        for v in list(response.values())[:-1]:
            agent_list.append({
                "agent": "/".join([v["author"], v["name"], v['version']])
            })

        return agent_list

    def check_agent_updates(self, author: str, name: str, current_version: str) -> bool:
        response = requests.get(f"{self.base_url}/cerebrum/check_updates", params={
            "author": author,
            "name": name,
            "current_version": current_version
        })
        response.raise_for_status()
        return response.json()["update_available"]

    def check_reqs_installed(self, agent_path: Path) -> bool:
        agent_package = AgentPackage(agent_path)
        agent_package.load()
        reqs_content = agent_package.files.get("meta_requirements.txt")
        if not reqs_content:
            return True  # No requirements file, consider it as installed

        try:
            result = subprocess.run(
                ['conda', 'list'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        except Exception:
            result = subprocess.run(
                ['pip', 'list', '--format=freeze'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        reqs = [line.strip().split("==")[0] for line in reqs_content.decode('utf-8').splitlines() if line.strip() and not line.startswith("#")]

        output = result.stdout.decode('utf-8')
        installed_packages = [line.split()[0]
                              for line in output.splitlines() if line]

        return all(req in installed_packages for req in reqs)

    def install_agent_reqs(self, agent_path: Path):
        agent_package = AgentPackage(agent_path)
        agent_package.load()
        reqs_content = agent_package.files.get("meta_requirements.txt")
        if not reqs_content:
            print("No meta_requirements.txt found. Skipping dependency installation.")
            return

        temp_reqs_path = self.cache_dir / "temp_requirements.txt"
        with open(temp_reqs_path, "wb") as f:
            f.write(reqs_content)

        log_path = agent_path.with_suffix('.log')

        print(f"Installing dependencies for agent. Writing to {log_path}")

        with open(log_path, "a") as f:
            subprocess.check_call([
                sys.executable,
                "-m",
                "pip",
                "install",
                "-r",
                str(temp_reqs_path)
            ], stdout=f, stderr=f)

        temp_reqs_path.unlink()  # Remove temporary requirements file

    def load_agent(self, 
                   author: str = '', 
                   name: str = '', 
                   version: str | None = None,
                   local: bool = False, 
                   path: str | None = None):
        
        if not local:
            if version is None:
                cached_versions = self._get_cached_versions(author, name)
                version = get_newest_version(cached_versions)

            agent_path = self._get_cache_path(author, name, version)
            
            if not agent_path.exists():
                print(f"Agent {author}/{name} (v{version}) not found in cache. Downloading...")
                self.download_agent(author, name, version)
        else:
            agent_path = path


        agent_package = AgentPackage(agent_path)
        agent_package.load()

        entry_point = agent_package.get_entry_point()
        module_name = agent_package.get_module_name()

        # Create a temporary directory to extract the agent files
        temp_dir = self.cache_dir / "temp" / f"{author}_{name}_{version}"
        temp_dir.mkdir(parents=True, exist_ok=True)

        # Extract agent files to the temporary directory
        for filename, content in agent_package.files.items():
            file_path = temp_dir / filename
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_bytes(content)

        # Add the temporary directory to sys.path
        sys.path.insert(0, str(temp_dir))

        # Load the module
        spec = importlib.util.spec_from_file_location(module_name, str(temp_dir / entry_point))
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        # Remove the temporary directory from sys.path
        sys.path.pop(0)

        # Get the agent class
        agent_class = getattr(module, module_name)
 
        return agent_class, agent_package.get_config()


if __name__ == '__main__':
    manager = AgentManager('https://my.aios.foundation/')
    agent = manager.download_agent('example', 'academic_agent')
    print(agent)