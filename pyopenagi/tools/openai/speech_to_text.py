import requests

import soundfile as sf

from ...utils.utils import get_from_env

from ..base import BaseHuggingfaceTool

class SpeechToText(BaseHuggingfaceTool):
    def __init__(self):
        super().__init__()

    def run(self, params):
        API_URL = "https://api-inference.huggingface.co/models/openai/whisper-large-v3"
        headers = {"Authorization": "Bearer " + get_from_env("HF_AUTH_TOKENS")}

        path = params["path"]

        data = sf.read(path)
        response = requests.post(API_URL, headers=headers, data=data)
        text = response.content
        return text

    def get_tool_call_format(self):
        tool_call_format = {
            "type": "function",
            "function": {
                "name": "speech_to_text",
                "description": "translate the voice into texts",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "path": {
                             "type": "string",
                             "description": "path of the saved audio"
                        }
                    },
                    "required": [
                        "path"
                    ]
                }
            }
        }
        return tool_call_format
