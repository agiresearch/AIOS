# This file contains helpful parsing utilities
# This is not used for now


class BaseParser:
    def __init__(self, llm, parser_type):
        self.llm = llm
        self.parser_type = parser_type

    def parse(self, instruction):
        pass

class PunctuationParser(BaseParser):
    def __init__(self, llm, parser_type = "punctuation"):
        pass

    def parse(self, instruction):
        """
        parse calls with different number of arguments
        1) command_type
        2) command_type command_name
        3) command_type command_name command_body
        """
        if ": " in instruction:
            splitted_command = instruction.split(": ")

            command_head = splitted_command[0].split(" ")
            command_body = splitted_command[-1]

            command_type = command_head[0]
            command_name = command_head[1]
            return {
                "command_type": command_type,
                "command_name": command_name,
                "command_body": command_body
            }

        elif " " in instruction:
            command_head = instruction.split(" ")

            command_type = command_head[0]
            command_name = command_head[1]
            return {
                "command_type": command_type,
                "command_name": command_name,
                "command_body": None
            }

        else:
            command_type = instruction
            return {
                "command_type": command_type,
                "command_name": None,
                "command_body": None
            }


class ChatGPTParser:
    def __init__(self, llm, parser_type = "gpt3.5"):
        pass

    def parse(self, instruction):
        pass
