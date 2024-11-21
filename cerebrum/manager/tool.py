import importlib
import os
import json
import base64
import subprocess
import sys
from typing import List, Dict, Optional, Tuple
import requests
from pathlib import Path
import platformdirs
import importlib.util

from cerebrum.manager.package import ToolPackage

class ToolManager:
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.base_path = os.path.dirname(os.path.abspath(__file__))
        self.cache_dir = Path(platformdirs.user_cache_dir("cerebrum_tools"))
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _version_to_path(self, version: str) -> str:
        return version.replace('.', '-')

    def _path_to_version(self, path_version: str) -> str:
        return path_version.replace('-', '.')

    def package_tool(self, folder_path: str) -> Dict:
        """Package a tool from a folder into a transportable format."""
        tool_files = self._get_tool_files(folder_path)
        metadata = self._get_tool_metadata(folder_path)
        
        # Validate required tool metadata
        required_fields = ['name', 'version', 'author']
        missing_fields = [field for field in required_fields 
                         if not metadata.get("meta", {}).get(field)]
        if missing_fields:
            raise ValueError(f"Missing required metadata fields: {missing_fields}")

        return {
            "author": metadata.get("meta", {}).get('author'),
            "name": metadata.get('name'),
            "version": metadata.get("meta", {}).get('version'),
            "license": metadata.get("license", "Unknown"),
            "files": tool_files,
            "entry": metadata.get("build", {}).get("entry", "tool.py"),
            "module": metadata.get("build", {}).get("module", "Tool"),
        }

    def upload_tool(self, payload: Dict):
        """Upload a tool to the remote server."""
        response = requests.post(f"{self.base_url}/cerebrum/tools/upload", json=payload)
        response.raise_for_status()
        print(f"Tool {payload.get('author')}/{payload.get('name')} (v{payload.get('version')}) uploaded successfully.")

    def download_tool(self, author: str, name: str, version: str | None = None) -> tuple[str, str, str]:
        """Download a tool from the remote server."""
        if version is None:
            cached_versions = self._get_cached_versions(author, name)
            version = self._get_newest_version(cached_versions)

        cache_path = self._get_cache_path(author, name, version)

        if cache_path.exists():
            print(f"Using cached version of tool {author}/{name} (v{version})")
            return author, name, version

        params = {
            "author": author,
            "name": name,
            "version": version
        } if version else {"author": author, "name": name}

        response = requests.get(f"{self.base_url}/cerebrum/tools/download", params=params)
        response.raise_for_status()
        tool_data = response.json()

        actual_version = tool_data.get('version', version)
        cache_path = self._get_cache_path(author, name, actual_version)

        self._save_tool_to_cache(tool_data, cache_path)
        print(f"Tool {author}/{name} (v{actual_version}) downloaded and cached successfully.")

        if not self.check_reqs_installed(cache_path):
            self.install_tool_reqs(cache_path)

        return author, name, actual_version

    def load_tool(self, author: str, name: str, version: str | None = None) -> Tuple[type, dict]:
        """Load a tool dynamically and return its class and configuration."""
        if version is None:
            cached_versions = self._get_cached_versions(author, name)
            version = self._get_newest_version(cached_versions)

        tool_path = self._get_cache_path(author, name, version)
        
        if not tool_path.exists():
            print(f"Tool {author}/{name} (v{version}) not found in cache. Downloading...")
            self.download_tool(author, name, version)

        tool_package = ToolPackage(tool_path)
        tool_package.load()

        # Get entry point and module name
        entry_point = tool_package.get_entry_point()
        module_name = tool_package.get_module_name()

        # Create temporary directory for tool files
        temp_dir = self.cache_dir / "temp" / f"{author}_{name}_{version}"
        temp_dir.mkdir(parents=True, exist_ok=True)

        # Extract tool files
        for filename, content in tool_package.files.items():
            file_path = temp_dir / filename
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_bytes(content)

        # Add to Python path and load module
        sys.path.insert(0, str(temp_dir))
        
        try:
            # Load the module
            spec = importlib.util.spec_from_file_location(module_name, str(temp_dir / entry_point))
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            # Get the tool class
            tool_class = getattr(module, module_name)
            
            return tool_class, tool_package.get_config()
        finally:
            # Clean up
            sys.path.pop(0)

    def _get_cached_versions(self, author: str, name: str) -> List[str]:
        """Get list of cached versions for a tool."""
        tool_dir = self.cache_dir / author / name
        if tool_dir.exists():
            return [self._path_to_version(v.stem) for v in tool_dir.glob("*.tool") if v.is_file()]
        return []

    def _get_newest_version(self, versions: List[str]) -> Optional[str]:
        """Get the newest version from a list of versions."""
        if not versions:
            return None
        # Simple version comparison (you might want to use packaging.version for more robust comparison)
        return sorted(versions, key=lambda v: [int(x) for x in v.split('.')])[-1]

    def _get_cache_path(self, author: str, name: str, version: str) -> Path:
        """Get the cache path for a tool."""
        return self.cache_dir / author / name / f"{self._version_to_path(version)}.tool"

    def _save_tool_to_cache(self, tool_data: Dict, cache_path: Path):
        """Save a tool to the local cache."""
        tool_package = ToolPackage(cache_path)
        tool_package.metadata = {
            "author": tool_data["author"],
            "name": tool_data["name"],
            "version": tool_data["version"],
            "license": tool_data["license"],
            "entry": tool_data["entry"],
            "module": tool_data["module"],
        }
        tool_package.files = {
            file["path"]: base64.b64decode(file["content"]) 
            for file in tool_data["files"]
        }
        tool_package.save()

    def _get_tool_files(self, folder_path: str) -> List[Dict[str, str]]:
        """Get all files from a tool folder."""
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

    def _get_tool_metadata(self, folder_path: str) -> Dict[str, str]:
        """Get tool metadata from config file."""
        config_path = os.path.join(folder_path, "config.json")
        if os.path.exists(config_path):
            with open(config_path, "r") as f:
                return json.load(f)
        return {}

    def check_reqs_installed(self, tool_path: Path) -> bool:
        """Check if tool requirements are installed."""
        tool_package = ToolPackage(tool_path)
        tool_package.load()
        reqs_content = tool_package.files.get("requirements.txt")
        
        if not reqs_content:
            return True  # No requirements file

        try:
            result = subprocess.run(
                ['pip', 'list', '--format=freeze'], 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE
            )
            installed_packages = [
                line.split('==')[0].lower() 
                for line in result.stdout.decode('utf-8').splitlines()
            ]
            required_packages = [
                line.strip().split('==')[0].lower()
                for line in reqs_content.decode('utf-8').splitlines()
                if line.strip() and not line.startswith('#')
            ]
            return all(req in installed_packages for req in required_packages)
        except Exception as e:
            print(f"Error checking requirements: {e}")
            return False

    def install_tool_reqs(self, tool_path: Path):
        """Install tool requirements."""
        tool_package = ToolPackage(tool_path)
        tool_package.load()
        reqs_content = tool_package.files.get("requirements.txt")
        
        if not reqs_content:
            print("No requirements.txt found. Skipping dependency installation.")
            return

        # Create temporary requirements file
        temp_reqs_path = self.cache_dir / "temp_requirements.txt"
        with open(temp_reqs_path, "wb") as f:
            f.write(reqs_content)

        # Install requirements
        try:
            subprocess.check_call([
                sys.executable,
                "-m",
                "pip",
                "install",
                "-r",
                str(temp_reqs_path)
            ])
            print("Tool requirements installed successfully.")
        except subprocess.CalledProcessError as e:
            print(f"Error installing requirements: {e}")
        finally:
            temp_reqs_path.unlink(missing_ok=True)

    def list_available_tools(self) -> List[Dict[str, str]]:
        """List all available tools from the remote server."""
        response = requests.get(f"{self.base_url}/cerebrum/tools/list")
        response.raise_for_status()
        tools = response.json()
        return [
            {
                "tool": f"{tool['author']}/{tool['name']}/{tool['version']}",
                "type": tool.get('tool_type', 'generic'),
                "description": tool.get('description', '')
            }
            for tool in tools
        ]

    def check_tool_updates(self, author: str, name: str, current_version: str) -> bool:
        """Check if updates are available for a tool."""
        response = requests.get(
            f"{self.base_url}/cerebrum/tools/check_updates",
            params={
                "author": author,
                "name": name,
                "current_version": current_version
            }
        )
        response.raise_for_status()
        return response.json()["update_available"]