from ...base import BaseRapidAPITool

from typing import Any, Dict, List, Optional

# from pydantic import root_validator

from src.utils.utils import get_from_env

import requests

class HotelSearchAPI(BaseRapidAPITool):
    def __init__(self):
        super().__init__()
        self.url = "https://hotels4.p.rapidapi.com/locations/v3/search"
        self.host_name = "hotels4.p.rapidapi.com"

        self.api_key = get_from_env("RAPID_API_KEY")

    def run(self, params):
        headers = {
            "X-RapidAPI-Key": self.api_key,
            "X-RapidAPI-Host": self.host_name
        }
        try:
            self.query_string = {
                "q": params["q"] # city
                # "locale": params["locale"]
            }
        except ValueError:
            raise KeyError(
                "The keys in params do not match the excepted keys in params for currency converter api. "
                "Please make sure it contains the key 'q'"
            )
        response = requests.get(self.url, headers=headers, params=self.query_string).json()

        result = self.parse_result(response)
        return result


    def parse_result(self, response) -> str:
        return "Completion hints are: " + ",".join(response["hints"].values())
