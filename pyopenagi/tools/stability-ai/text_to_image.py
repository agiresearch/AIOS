from ...utils.utils import get_from_env

from ..base import BaseHuggingfaceTool

import requests

class TextToImage(BaseHuggingfaceTool):
    def __init__(self):
        super().__init__()

    def run(self, params):

        API_URL = "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-xl-base-1.0"
        headers = {"Authorization": "Bearer " + get_from_env("HF_AUTH_TOKENS")}

        prompt = params["prompt"]

        path = params["path"]

        payload = {
            "inputs": prompt
        }
        response = requests.post(API_URL, headers=headers, json=payload)

        image_bytes = response.content
        # You can access the image with PIL.Image for example
        import io
        from PIL import Image

        image = Image.open(io.BytesIO(image_bytes))
        image.save(path)

        return f"a generated image saved at {path}"

    def get_tool_call_format(self):
        tool_call_format = {
            "type": "function",
            "function": {
                "name": "text_to_image",
                "description": "generate images with the given texts",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "prompt": {
                            "type": "string",
                            "description": "prompt description of the image to be generated"
                        },
                        "path": {
                             "type": "string",
                             "description": "path to save the generated image"
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
