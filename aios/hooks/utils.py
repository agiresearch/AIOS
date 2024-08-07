import random
import string

def generate_random_string(length: int = 6) -> str:
    return ''.join(random.choices(string.ascii_letters, k=length))
