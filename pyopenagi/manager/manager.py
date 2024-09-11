# agent_manager.py

import os
import json
import base64
import subprocess
import sys
from typing import List, Dict
import requests
from pathlib import Path

class AgentManager:
    def __init__(self, base_url: str):
        self.base_url = base_url
        # self.cache_dir = Path(user_cache_dir("agent_manager", "AIOS"))
        self.cache_dir = Path('/Users/rama2r/AIOS/agenthub/cache')
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def upload_agent(self, author: str | None, name: str | None, version: str | None, folder_path: str):
        agent_files = self._get_agent_files(folder_path)
        metadata = self._get_agent_metadata(folder_path)


        payload = {
            "author":  metadata.get("meta", {}).get('author', author),
            "name":  metadata.get('name', name),
            "version": metadata.get("meta", {}).get('version', version),
            "license": metadata.get("license", "Unknown"),
            "files": agent_files,
            "entry": metadata.get("build", {}).get("entry", "main.py"),
            "module": metadata.get("build", {}).get("module", "Agent")
        }

        response = requests.post(f"{self.base_url}/api/upload", json=payload)
        response.raise_for_status()
        print(f"Agent {payload.get('author')}/{payload.get('name')} (v{payload.get('version')}) uploaded successfully.")

    def download_agent(self, author: str, name: str, version: str = "latest") -> str:
        cache_path = self._get_cache_path(author, name, version)
        if cache_path.exists():
            print(f"Using cached version of {author}/{name} (v{version})")
        else:
            response = requests.get(f"{self.base_url}/api/download", params={
                "author": author,
                "name": name,
                "version": version
            })
            response.raise_for_status()
            agent_data = response.json()

            self._save_agent_to_cache(agent_data, cache_path)
            print(f"Agent {author}/{name} (v{version}) downloaded successfully.")

        if not self.check_reqs_installed(cache_path):
            self.install_agent_reqs(cache_path)

        return str(cache_path)

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

    def _get_cache_path(self, author: str, name: str, version: str) -> Path:
        return self.cache_dir / author / name / version

    def _save_agent_to_cache(self, agent_data: Dict, cache_path: Path):
        cache_path.mkdir(parents=True, exist_ok=True)
        for file_data in agent_data["files"]:
            file_path = cache_path / file_data["path"]
            file_path.parent.mkdir(parents=True, exist_ok=True)
            with open(file_path, "wb") as f:
                f.write(base64.b64decode(file_data["content"]))

    def list_available_agents(self) -> List[Dict[str, str]]:
        response = requests.get(f"{self.base_url}/api/list_agents")
        response.raise_for_status()
        return response.json()

    def check_agent_updates(self, author: str, name: str, current_version: str) -> bool:
        response = requests.get(f"{self.base_url}/api/check_updates", params={
            "author": author,
            "name": name,
            "current_version": current_version
        })
        response.raise_for_status()
        return response.json()["update_available"]

    def check_reqs_installed(self, agent_path: Path) -> bool:
        reqs_path = agent_path / "meta_requirements.txt"
        if not reqs_path.exists():
            return True  # No requirements file, consider it as installed

        try:
            result = subprocess.run(['conda', 'list'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        except Exception:
            result = subprocess.run(['pip', 'list', '--format=freeze'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        with open(reqs_path, "r") as f:
            reqs = [line.strip().split("==")[0] for line in f if line.strip() and not line.startswith("#")]

        output = result.stdout.decode('utf-8')
        installed_packages = [line.split()[0] for line in output.splitlines() if line]

        return all(req in installed_packages for req in reqs)

    def install_agent_reqs(self, agent_path: Path):
        reqs_path = agent_path / "meta_requirements.txt"
        if not reqs_path.exists():
            print("No meta_requirements.txt found. Skipping dependency installation.")
            return

        log_path = agent_path / "deplogs.txt"

        print(f"Installing dependencies for agent. Writing to {log_path}")

        with open(log_path, "a") as f:
            subprocess.check_call([
                sys.executable,
                "-m",
                "pip",
                "install",
                "-r",
                str(reqs_path)
            ], stdout=f, stderr=f)

if __name__ == '__main__':
    manager = AgentManager('http://localhost:3000')
    # manager.upload_agent('Balaji R', 'Cool Agent', '0.0.1', '/Users/rama2r/AIOS/pyopenagi/agents/example/academic_agent')
    # manager.upload_agent(None, None, None, '/Users/rama2r/AIOS/pyopenagi/agents/example/academic_agent')
    downloaded_path = manager.download_agent('example', 'academic_agent', '0.0.1')
    # print(f"Agent downloaded to: {downloaded_path}")