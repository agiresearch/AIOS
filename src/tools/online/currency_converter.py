from src.tools.base import BaseRapidAPITool

from typing import Any, Dict, List, Optional

# from pydantic import root_validator

from src.utils.utils import get_from_env

import requests

import os

class CurrencyConverterAPI(BaseRapidAPITool):
    def __init__(self):
        super().__init__()
        self.url = "https://currency-conversion-and-exchange-rates.p.rapidapi.com/latest"
        self.host_name = "currency-conversion-and-exchange-rates.p.rapidapi.com"
        self.api_key = get_from_env("CURRENT_CONVERTER_API_KEY")

    def run(self, params: dict):
        headers = {
            "X-RapidAPI-Key": self.api_key,
            "X-RapidAPI-Host": self.host_name
        }

        self.query_string = params

        response = requests.get(self.url, headers=headers, params=self.query_string)

        response = requests.get(self.url, headers=headers, params=self.query_string)
        result = self.parse_result(response)
        return result

    def parse_result(self, response) -> str:
        results = []
        for k,v in response["rates"]:
            results.append(f"Currency from {response["base"]} to {k} is {v}.")
        return " ".join(results)