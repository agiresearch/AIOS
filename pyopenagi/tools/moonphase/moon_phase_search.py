from ..base import BaseRapidAPITool

from pyopenagi.utils.utils import get_from_env

import requests

class MoonPhaseSearch(BaseRapidAPITool):
    def __init__(self):
        super().__init__()
        self.url = "https://moon-phase.p.rapidapi.com/basic"
        self.host_name = "moon-phase.p.rapidapi.com"
        self.api_key = get_from_env("RAPID_API_KEY")

    def run(self):
        headers = {
            "X-RapidAPI-Key": self.api_key,
            "X-RapidAPI-Host": self.host_name
        }
        response = requests.get(self.url, headers=headers)

        result = self.parse_result(response)
        return result

    def parse_result(self, response) -> str:
        return f'Current moon phase is {response["phase_name"]}. It has {response["days_until_next_full_moon"]} until next full moon. It has {response["days_until_next_new_moon"]} until the next new moon.'
