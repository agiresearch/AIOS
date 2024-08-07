import gzip
import base64
import subprocess
import sys
import json
import pprint
import requests
import argparse
import os

class Interactor:
    def __init__(self, base_folder="./"):
        script_path = os.path.abspath(__file__)
        script_dir = os.path.dirname(script_path)
        self.base_folder = os.path.join(script_dir, base_folder)

    def upload_agent(self, agent_name):
        agent_dir = os.path.join(self.base_folder, agent_name)

        author, name = agent_name.split("/")

        config_file = os.path.join(agent_dir, "config.json")
        with open(config_file, 'r') as f:
            config_data: dict[str, dict] = json.load(f)
        
        # print(config_data)

        meta_data = config_data.get('meta')

        headers = {
            "Content-Type": "application/json",
        }

        # compress python code
        encoded_code = self.compress(
            self.minify_python_code(agent_dir)
        )

        # compress meta_requirements.txt
        encoded_reqs =  self.compress(
            self.minify_reqs(agent_dir)
        )

        # compress config.json
        config_str = json.dumps(config_data)
        encoded_config = self.compress(config_str)

        upload_content = {
            'author': author,
            'name': name,
            'version': float(meta_data.get('version')),
            'license': meta_data.get('license'),
            'config': encoded_config,
            'code': encoded_code,
            'dependencies': encoded_reqs
        }

        url = 'https://openagi-beta.vercel.app/api/upload'

        pprint.pprint(upload_content)

        response = requests.post(
            url,
            data=json.dumps(upload_content),
            headers=headers
        )
        
        pprint.pprint(response.content)

    def minify_python_code(self, agent_dir):
        code_path = os.path.join(agent_dir, "agent.py")
        with open(code_path, 'r') as file:
            lines: list[str] = file.readlines()
        minified_lines = []
        for line in lines:
            stripped_line = line.rstrip()
            if stripped_line and not stripped_line.lstrip().startswith("#"):
                minified_lines.append(stripped_line)
        minified_code = "\n".join(minified_lines)
        return minified_code

    def minify_reqs(self, agent_dir):
        req_path = os.path.join(agent_dir, "meta_requirements.txt")
        with open(req_path, 'r') as file:
            self.reqs: str = file.read()
        cleaned = [line.strip() for line in self.reqs.split(
            '\n') if line.strip() and not line.startswith('#')]
        minified_reqs = ';'.join(cleaned)
        return minified_reqs
    
    def minify_config(self, config_data):
        minified_config = self.compress(config_data)
        return minified_config

    def compress(self, minified_data):
        compressed_data = gzip.compress(minified_data.encode('utf-8'))
        encoded_data = base64.b64encode(compressed_data)
        encoded_data = encoded_data.decode('utf-8')
        return encoded_data

    # download agent
    def download_agent(self, agent_name):
        assert "/" in agent_name, 'agent_name should in the format of "author/agent_name"'
        author, name = agent_name.split("/")
        # print(author, name)
        print(author)
        print(name)
        query = f'https://openagi-beta.vercel.app/api/download?author={author}&name={name}'
        response = requests.get(query)
        print(response)
        response: dict = response.json()

        agent_folder = os.path.join(self.base_folder, agent_name)

        if not os.path.exists(agent_folder):
            os.makedirs(agent_folder)

        encoded_config = response.get('config')
        encoded_code = response.get("agent_code")
        encoded_reqs = response.get('dependencies')

        self.download_config(
            self.decompress(encoded_config),
            agent_name
        )
        self.download_code(
            self.decompress(encoded_code),
            agent_name
        )
        self.download_reqs(
            self.decompress(encoded_reqs),
            agent_name
        )

    def decompress(self, encoded_data):
        compressed_data = base64.b64decode(encoded_data)
        decompressed_data = gzip.decompress(compressed_data)
        decompressed_data.replace(";", "\n")
        return decompressed_data

    def download_config(self, config_data, agent_name) :
        config_path = os.path.join(self.base_folder, agent_name, "config.json")
        with open(config_path, "w", "utf-8") as w:
            json.dump(config_data, w, indent=2)

    def download_reqs(self, reqs_data, agent_name):
        reqs_path = os.path.join(self.base_folder, agent_name, "meta_requirements.txt")

        with open(reqs_path, 'w') as file:
            file.write(reqs_data)

        subprocess.check_call([sys.executable, "-m", "pip install -r", reqs_path])

    def download_code(self):
        compressed_data = base64.b64decode(self.encoded_string)
        decompressed_data = gzip.decompress(compressed_data)

        with open(self.output_file_path, 'w', newline='') as file:
            file.write(decompressed_data.decode('utf-8'))

        return self
    
def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", required=True, choices=["download", "upload"])
    parser.add_argument("--agent_name", required=True, 
        help="agent_name should be named as author/name in order for deduplication"
    )
    args = parser.parse_args()
    return args

if __name__ == '__main__':
    args = parse_args()
    mode = args.mode
    agent_name = args.agent_name

    client = Interactor()
    if mode == "download":
        client.download_agent(agent_name)
    else:
        assert mode == "upload"
        client.upload_agent(agent_name)