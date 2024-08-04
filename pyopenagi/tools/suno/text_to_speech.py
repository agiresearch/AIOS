import requests

from ...utils.utils import get_from_env

from ..base import BaseHuggingfaceTool

class TextToSpeech(BaseHuggingfaceTool):
    def __init__(self):
        super().__init__()

    def run(self, params):
        API_URL = "https://api-inference.huggingface.co/models/suno/bark"
        headers = {"Authorization": "Bearer " + get_from_env("HF_AUTH_TOKENS")}

        prompt = params["prompt"]
        path = params["path"]

        payload = {
             "prompt": prompt
        }

        response = requests.post(API_URL, headers=headers, json=payload)

        with open(path,"wb") as f:
            f.write(response.content)

        return f"a generated audio saved at {path}"
        # pass

    def get_tool_call_format(self):
        tool_call_format = {
            "type": "function",
            "function": {
                "name": "text_to_speech",
                "description": "generate voice based on the text",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "prompt": {
                             "type": "string",
                             "description": "text description"
                        },
                        "path": {
                             "type": "string",
                             "description": "path to save the audio"
                        }
                    },
                    "required": [
                        "prompt",
                        "path"
                    ]
                }
            }
        }
        return tool_call_format
