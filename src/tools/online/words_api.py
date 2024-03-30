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
        self.api_key = get_from_env("WORDS_API_KEY")
    
    def run(self, params):
        headers = {
            "X-RapidAPI-Key": self.api_key,
            "X-RapidAPI-Host": self.host_name
        }
        assert params["words"] is not None and params["api_name"] is not None
        self.words = params["words"]
        self.api_name = params["api_name"]
        self.url = os.path.join(self.url, params["words"], params["api_name"])
        response = requests.get(self.url, headers=headers)
        result = self.parse_result(response)
        return result

    def parse_result(self, response) -> str:
        return response["words"] + " " + self.api_name + "[" + ",".join(response[self.api_name]) + "]"