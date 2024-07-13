from ..base import BaseRapidAPITool

from pyopenagi.utils.utils import get_from_env

import requests

import json

class AirportSearch(BaseRapidAPITool):
    def __init__(self):
        super().__init__()
        self.url = "https://tripadvisor16.p.rapidapi.com/api/v1/flights/searchAirport"
        self.host_name = "tripadvisor16.p.rapidapi.com"
        self.api_key = get_from_env("RAPID_API_KEY")

    def run(self, params: dict):
        headers = {
            "X-RapidAPI-Key": self.api_key,
            "X-RapidAPI-Host": self.host_name
        }
        try:
            self.query_string = {
                "query": params["query"],
            }
        except ValueError:
            raise KeyError(
                "The keys in params do not match the excepted keys in params for tripadvisor search airport api. "
                "Please make sure it contains the key: 'query'"
            )

        # print(self.query_string)

        response = requests.get(self.url, headers=headers, params=self.query_string).json()
        return self.parse_result(response)

    def parse_result(self, response) -> str:
        limited_results = response['data'][:2]

        simplified_results = []
        for result in limited_results:
            simplified_result = {
                'name': result['name'],
                'airportCode': result['airportCode'],
                'coords': result['coords']
            }
            simplified_results.append(simplified_result)

        return json.dumps(simplified_results)

    def get_tool_call_format(self):
        tool_call_format = {
			"type": "function",
			"function": {
				"name": "airport_search",
				"description": "Search for an airport by query",
				"parameters": {
					"type": "object",
					"properties": {
						"query": {
							"type": "string",
							"description": "Search query for airport"
						}
					},
					"required": [
						"query"
					]
				}
			}
		}
        return tool_call_format
