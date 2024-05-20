import tiktoken
from groq import Groq
import os
from dotenv import load_dotenv

load_dotenv()

def get_token_length(string: str) -> int:
    encoding = tiktoken.get_encoding("cl100k_base")
    num_tokens = len(encoding.encode(string))
    return num_tokens

def get_intended_speed(phrase: str) -> float:
    client = Groq(
        api_key=os.environ.get("GROQ_API_KEY"),
    )

    chat_completion = client.chat.completions.create(
        messages=[
            {
                "role": "user",
                "content": f"Given the phrase \"{phrase}\" \n Output the urgency of the request as a decimal between 0.0 (means that the request can be filled in no rush at all) and 1.0 (means the request needs to be filled DOUBLE ASAP). Output only the decimal, nothing else.",
            }
        ],
        model="llama3-8b-8192",
    )

    return float(chat_completion.choices[0].message.content)