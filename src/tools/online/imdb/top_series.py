from src.tools.base import BaseRapidAPITool

from typing import Any, Dict, List, Optional

# from pydantic import root_validator

from src.utils.utils import get_from_env

import requests

class TopSeriesAPI(BaseRapidAPITool):
    def __init__(self):
        super().__init__()
        self.url = "https://imdb-top-100-movies.p.rapidapi.com/series/"
        self.host_name = "imdb-top-100-movies.p.rapidapi.com"

        self.api_key = get_from_env("RAPID_API_KEY")

    def run(self, k):
        headers = {
            "X-RapidAPI-Key": self.api_key,
            "X-RapidAPI-Host": self.host_name
        }
        response = requests.get(self.url, headers=headers)
        result = self.parse_result(response, k)
        return result


    def parse_result(self, response, k) -> str:
        result = []
        for i in range(k):
            result.append(response[str(i)]["title"])

        return f"Top {k} series ranked by IMDB are: " + ",".join(result)
