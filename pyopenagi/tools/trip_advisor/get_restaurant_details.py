from ..base import BaseRapidAPITool

from pyopenagi.utils.utils import get_from_env

import requests

import json

class GetRestaurantDetails(BaseRapidAPITool):
    def __init__(self):
        super().__init__()
        self.url = "https://tripadvisor16.p.rapidapi.com/api/v1/restaurant/getRestaurantDetails"
        self.host_name = "tripadvisor16.p.rapidapi.com"
        self.api_key = get_from_env("RAPID_API_KEY")

    def run(self, params: dict):
        headers = {
            "X-RapidAPI-Key": self.api_key,
            "X-RapidAPI-Host": self.host_name
        }

        try:
            self.query_string = {
                "restaurantsId": params["restaurantsId"],
            }
        except ValueError:
            raise KeyError(
                "The keys in params do not match the excepted keys in params for tripadvisor get restaurant details api. "
                "Please make sure it contains the key: 'restaurantsID'"
            )

        response = requests.get(self.url, headers=headers, params=self.query_string).json()
        return self.parse_result(response)


    def parse_result(self, response) -> str:
        location = response["data"]["location"]

        useful_info = {
            "name": location.get("name"),
            "latitude": location.get("latitude"),
            "longitude": location.get("longitude"),
            "num_reviews": location.get("num_reviews"),
            "rating": location.get("rating"),
            "price_level": location.get("price_level"),
            "address": location.get("address"),
            "phone": location.get("phone"),
            "website": location.get("website"),
            "cuisine": [cuisine["name"] for cuisine in location.get("cuisine", [])],
            "hours": location.get("hours", {}).get("week_ranges", [])
            }
        return json.dumps(useful_info)

    def get_tool_call_format(self):
        tool_call_format = {
			"type": "function",
			"function": {
				"name": "get_restaurant_details",
				"description": "Provides details about a restaurant",
				"parameters": {
					"type": "object",
					"properties": {
						"restaurantsId": {
							"type": "string",
							"description": "The ID of the restaurant to get details for"
						}
					},
					"required": [
						"restaurantsId"
					]
				}
			}
		}
        return tool_call_format
