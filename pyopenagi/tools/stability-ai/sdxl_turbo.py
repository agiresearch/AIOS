from diffusers import AutoPipelineForText2Image
import torch

from ..base import BaseHuggingfaceTool

class SdxlTurbo(BaseHuggingfaceTool):
    def __init__(self):
        super().__init__()
        self.pipe = AutoPipelineForText2Image.from_pretrained("stabilityai/sdxl-turbo", torch_dtype=torch.float16, variant="fp16")

    def run(self, params):
        prompt = params["prompt"]
        self.pipe.to("cuda")
        image = self.pipe(prompt=prompt, num_inference_steps=1, guidance_scale=0.0).images[0]
        return image

    def get_tool_call_format(self):
        tool_call_format = {
            "type": "function",
            "function": {
                "name": "sdxl_turbo",
                "description": "generate images with the given texts",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "prompt": {
                            "type": "string",
                            "description": "prompt description of the image to be generated"
                        }
                    },
                    "required": [
                        "prompt"
                    ]
                }
            }
        }
        return tool_call_format
