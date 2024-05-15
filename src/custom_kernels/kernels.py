from src.custom_kernels.base import BaseKernel
from src.custom_kernels.cache import Cache
from openai import OpenAI
import os

class GPTKernel(BaseKernel):
    def __init__(self, name: str):
        self.cache = Cache()
        self.client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

    # def 