import litellm
import os
from litellm import batch_completion

from dotenv import load_dotenv

load_dotenv()

responses = batch_completion(
    model="gpt-4o-mini",
    messages = [
        [
            {
                "role": "user",
                "content": "good morning? "
            }
        ],
        [
            {
                "role": "user",
                "content": "what's the time? "
            }
        ]
    ]
)