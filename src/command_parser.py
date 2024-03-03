import os

class BaseParser:
    def __init__(self, llm, parser_type):
        self.llm = llm
        self.parser_type = parser_type

    def parse(self, instruction):
        pass

class Parser:
    def __init__(self, llm, parser_type = "base"):
        pass

    def parse(self, instruction):
        command = instruction.split(" ")
        command_name = command[0]
        command_content = command[1]
        return (command_name, command_content)


class ChatGPTParser:
    def __init__(self, llm, parser_type = "base"):
        pass

    def parse(self, instruction):
        pass