from PIL import Image
import torch
from diffusers import StableDiffusionInstructPix2PixPipeline, EulerAncestralDiscreteScheduler

from ..base import BaseHuggingfaceTool

class ImageToImage(BaseHuggingfaceTool):
    def __init__(self):
        super().__init__()
        self.model_id = "timbrooks/instruct-pix2pix"
        self.pipe = StableDiffusionInstructPix2PixPipeline.from_pretrained(self.model_id, torch_dtype=torch.float16, safety_checker=None)
        self.pipe.to("cuda")
        self.pipe.scheduler = EulerAncestralDiscreteScheduler.from_config(self.pipe.scheduler.config)

    def run(self, params):
        path = params["old_path"]
        image = Image.open(path)
        prompt = params["prompt"]
        new_image = self.pipe(prompt, image=image, num_inference_steps=10, image_guidance_scale=1).images
        new_path = params["new_path"]
        new_image.save(path)
        return f"a new image saved at {new_path}"

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
                        "old_path": {
                            "type": "string",
                            "description": "path to load the old image"
                        },
                        "new_path": {
                            "type": "string",
                            "description": "path to save the new generated image"
                        }
                    },
                    "required": [
                        "prompt",
                        "old_path",
                        "new_path"
                    ]
                }
            }
        }
        return tool_call_format
