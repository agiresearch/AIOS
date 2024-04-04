from src.tools.base import BaseRapidAPITool

from typing import Any, Dict, List, Optional

# from pydantic import root_validator

from src.utils.utils import get_from_env

import requests

import os

class WordsAPI(BaseRapidAPITool):
    def __init__(self):
        super().__init__()
        self.url = "https://wordsapiv1.p.rapidapi.com/words/"
        self.host_name = "wordsapiv1.p.rapidapi.com"
        self.api_key = get_from_env("RAPID_API_KEY")

    def run(self, params):
        headers = {
            "X-RapidAPI-Key": self.api_key,
            "X-RapidAPI-Host": self.host_name
        }
        try:
            self.word = params["word"]
            self.api_name = params["api_name"]
        except KeyError:
            raise KeyError(
                "The keys in params do not match the excepted keys in params for words api. "
                "Please make sure it contains two keys: 'words' and 'api_name'"
            )
        self.url = os.path.join(self.url, self.word, self.api_name)

        response = requests.get(self.url, headers=headers).json()
        result = self.parse_result(response)
        return result

    def parse_result(self, response) -> str:
        return response["word"] + " " + self.api_name + " [" + ",".join(response[self.api_name]) + "]"
