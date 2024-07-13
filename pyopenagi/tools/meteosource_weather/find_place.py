from ..base import BaseRapidAPITool

# from pydantic import root_validator

from pyopenagi.utils.utils import get_from_env

import requests

class SongAutocompleteAPI(BaseRapidAPITool):
    def __init__(self):
        super().__init__()
        self.url = "https://ai-weather-by-meteosource.p.rapidapi.com/find_places"
        self.host_name = "ai-weather-by-meteosource.p.rapidapi.com"

        self.api_key = get_from_env("RAPID_API_KEY")

    def run(self, params):
        headers = {
            "X-RapidAPI-Key": self.api_key,
            "X-RapidAPI-Host": self.host_name
        }
        try:
            self.query_string = {
                "text": params["text"],
                "language": params["language"]
            }
        except ValueError:
            raise KeyError(
                "The keys in params do not match the excepted keys in params for weather find place api. "
                "Please make sure it contains two keys: 'text' and 'language'"
            )
        response = requests.get(self.url, headers=headers, params=self.query_string).json()

        result = self.parse_result(response)
        return result


    def parse_result(self, response) -> str:
        location = [
            response["radm_area1"],
            response["adm_area2"],
            response["country"],
            response["lat"],
            response["lon"]
        ]
        return f"Found place of {response["name"]}: " + ",".join(location)
