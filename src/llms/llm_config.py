import pickle
import os
import json
from pathlib import Path

class LLMMeta:
    config_location: str = os.path.dirname(os.path.abspath(__file__))+'/models_config.pkl'

    def __init__(self, name: str, provider: str, type: str ='casual_lm'):
        self.name = name
        self.provider = provider
        self.type = type

    def __repr__(self):
        return f"""
        Model Name: {self.name}
        Model Provider: {self.provider}
        Model Type: {self.type} """

    def _add_to_datasource(self):
        with open(self.config_location, "rb") as file:
            models: dict = pickle.load(file)

        models[self.name] = self

        with open(self.config_location, "wb") as file:
            pickle.dump(models, file)

    @classmethod
    def remove_model_from_datasource(cls, model_name: str):
        with open(cls.config_location, "rb") as file:
            models: dict = pickle.load(file)

        del models[model_name]

        with open(cls.config_location, "wb") as file:
            pickle.dump(models, file)

def process_json_files(directory_path):
    for filename in os.listdir(directory_path):
        if filename.endswith(".json"):
            file_path = os.path.join(directory_path, filename)
            with open(file_path, "r") as file:
                data = json.load(file)
                model_type = data["model_type"]
                open_sourced = data["open_sourced"]
                model_name = data["model_name"]

                if open_sourced:
                    provider = "huggingface"
                elif 'gpt' in model_name:
                    provider = "openai"
                elif 'bedrock' in model_name:
                    provider = 'aws'
                elif 'gemini' in model_name or 'gemma' in model_name:
                    provider = 'google'
                else:
                    print(f'Uncaught Model @ {model_name}')

                llm_meta = LLMMeta(name=model_name, provider=provider, type=model_type)
                llm_meta._add_to_datasource()

#run this once to generate from existing json config files
if __name__ == '__main__':
    directory_path = Path(f"{os.path.dirname(os.path.abspath(__file__))}/llm_config/")

    if not os.path.exists(f"{LLMMeta.config_location}"):
        with open(f"{LLMMeta.config_location}", 'wb') as file:
            pickle.dump({}, file)


    process_json_files(directory_path)
