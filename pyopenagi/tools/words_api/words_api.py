from ..base import BaseRapidAPITool

# from pydantic import root_validator

from pyopenagi.utils.utils import get_from_env

import requests

SUPPORTED_APIS = [
    "typeOf", "hasTypes", "partOf", "hasParts",
    "instanceOf", "hasInstances", "similarTo",
    "also", "entails", "memberOf", "hasMembers",
    "substanceOf", "hasSubstances", "inCategory",
    "hasCategories", "usageOf", "hasUsages",
    "inRegion", "regionOf", "pertainsTo", "synonyms",
    "examples", "antonyms", "pronunciation",
]

class WordsAPI(BaseRapidAPITool):
    def __init__(self):
        super().__init__()
        self.base_url = "https://wordsapiv1.p.rapidapi.com/words/"
        self.url = self.base_url
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

        if not self.is_supported(self.api_name):
            raise ValueError(
                f"{self.api_name} is currently not supported!"
            )

        self.url = f"{self.base_url}{self.word}/{self.api_name}"
        response = requests.get(self.url, headers=headers).json()
        result = self.parse_result(response)
        return result

    def parse_result(self, response) -> str:
        # fail response: {'success': False, 'message': 'word not found'}
        if "success" in response and not response["success"]:
            return response["message"]

        return response["word"] + " " + self.api_name + " [" + ",".join(response[self.api_name]) + "]"

    def is_supported(self, api_name):
        return api_name in SUPPORTED_APIS
