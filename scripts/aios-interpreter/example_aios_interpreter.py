import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from interpreter import interpreter

interpreter.llm.model = "gpt-4o-mini"
interpreter.chat("Calculate 10 * 20 / 2")  # Executes a single command
# interpreter.chat() # Starts an interactive chat
