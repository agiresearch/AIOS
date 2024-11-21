import json
from pathlib import Path
import zipfile
import os

class AgentPackage:
    def __init__(self, path: Path):
        self.path = path
        self.metadata = {}
        self.files = {}

    def load(self):
        with zipfile.ZipFile(self.path, 'r') as zip_ref:
            self.metadata = json.loads(zip_ref.read('metadata.json').decode('utf-8'))
            for file_info in zip_ref.infolist():
                if file_info.filename != 'metadata.json':
                    self.files[file_info.filename] = zip_ref.read(file_info.filename)

    def save(self):
        directory = os.path.dirname(self.path)

        os.makedirs(directory, exist_ok=True)

        with zipfile.ZipFile(self.path, 'w') as zip_ref:
            zip_ref.writestr('metadata.json', json.dumps(self.metadata))
            for filename, content in self.files.items():
                zip_ref.writestr(filename, content)

    def get_entry_point(self):
        return self.metadata.get('entry', 'agent.py')

    def get_module_name(self):
        return self.metadata.get('module', 'Agent')
    
    def get_config(self):
        return self.metadata
    

class ToolPackage:
    def __init__(self, path: Path):
        self.path = path
        self.metadata = {}
        self.files = {}

    def load(self):
        with zipfile.ZipFile(self.path, 'r') as zip_ref:
            self.metadata = json.loads(zip_ref.read('metadata.json').decode('utf-8'))
            for file_info in zip_ref.infolist():
                if file_info.filename != 'metadata.json':
                    self.files[file_info.filename] = zip_ref.read(file_info.filename)

    def save(self):
        directory = os.path.dirname(self.path)
        os.makedirs(directory, exist_ok=True)
        
        with zipfile.ZipFile(self.path, 'w') as zip_ref:
            zip_ref.writestr('metadata.json', json.dumps(self.metadata))
            for filename, content in self.files.items():
                zip_ref.writestr(filename, content)

    def get_entry_point(self) -> str:
        return self.metadata.get('entry', 'tool.py')

    def get_module_name(self) -> str:
        return self.metadata.get('module', 'Tool')
    
    def get_config(self) -> dict:
        return self.metadata
