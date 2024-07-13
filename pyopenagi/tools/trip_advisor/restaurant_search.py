

from ..base import BaseRapidAPITool

from pyopenagi.utils.utils import get_from_env

import requests

import json

class RestaurantSearch(BaseRapidAPITool):
    def __init__(self):
        super().__init__()
        self.url = "https://tripadvisor16.p.rapidapi.com/api/v1/restaurant/searchRestaurants"
        self.host_name = "tripadvisor16.p.rapidapi.com"
        self.api_key = get_from_env("RAPID_API_KEY")

    def run(self, params: dict):
        headers = {
            "X-RapidAPI-Key": self.api_key,
            "X-RapidAPI-Host": self.host_name
        }

        try:
            self.query_string = {
                "locationId": params["locationId"]
            }
        except ValueError:
            raise KeyError(
                "The keys in params do not match the excepted keys in params for tripadvisor search restaurant api. "
                "Please make sure it contains following required keys: "
                "locationID",
            )

        response = requests.get(self.url, headers=headers, params=self.query_string).json()
        return self.parse_result(response)

    def parse_result(self, response) -> str:
        limited_results = response['data']['data'][:2]

        simplified_results = []
        for result in limited_results:
            simplified_result = {
                'restaurantsId': result['restaurantsId'],
                'name': result['name'],
                'averageRating': result['averageRating'],
                'userReviewCount': result['userReviewCount'],
                'priceTag': result['priceTag'],
                'establishmentTypeAndCuisineTags': result['establishmentTypeAndCuisineTags']
            }
            simplified_results.append(simplified_result)

        return json.dumps(simplified_results)

    def get_tool_call_format(self):
        tool_call_format = {
			"type": "function",
			"function": {
				"name": "restaurant_search",
				"description": "Search for a restaurant by locationID",
				"parameters": {
					"type": "object",
					"properties": {
						"locationId ": {
							"type": "string",
							"description": "The locationID of the restaurant to search for"
						}
					},
					"required": [
						"locationId"
					]
				}
			}
		}
        return tool_call_format
