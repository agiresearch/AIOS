from ..base import BaseRapidAPITool

from pyopenagi.utils.utils import get_from_env

import requests

import json

class HotelSearch(BaseRapidAPITool):
    def __init__(self):
        super().__init__()
        self.url = "https://tripadvisor16.p.rapidapi.com/api/v1/hotels/searchHotels"
        self.host_name = "tripadvisor16.p.rapidapi.com"
        self.api_key = get_from_env("RAPID_API_KEY")

    def run(self, params: dict):
        headers = {
            "X-RapidAPI-Key": self.api_key,
            "X-RapidAPI-Host": self.host_name
        }

        try:
            self.query_string = {
                "geoId": params["geoId"],
                "checkIn": params["checkIn"],
                "checkOut": params["checkOut"],
            }
        except ValueError:
            raise KeyError(
                "The keys in params do not match the excepted keys in params for tripadvisor search hotel api. "
                "Please make sure it contains following required keys: "
                "geoId",
                "checkIn",
                "checkOut",
            )

        response = requests.get(self.url, headers=headers, params=self.query_string).json()
        return self.parse_result(response)


    def parse_result(self, response) -> str:
        if 'data' in response and 'data' in response['data']:
            hotels_data = response['data']['data'][:2]
            relevant_info = []
            for hotel in hotels_data:
                relevant_info.append({
                    'id': hotel['id'],
                    'title': hotel['title'],
                    'secondaryInfo': hotel['secondaryInfo'],
                    'bubbleRating': hotel['bubbleRating'],
                    'priceForDisplay': hotel['priceForDisplay'],
                    'priceDetails': hotel['priceDetails'],
                    'priceSummary': hotel['priceSummary']
                })
            return json.dumps(relevant_info)
        else:
            return json.dumps([])

    def get_tool_call_format(self):
        tool_call_format = {
			"type": "function",
			"function": {
				"name": "hotel_search",
				"description": "Provides details about a hotel",
				"parameters": {
					"type": "object",
					"properties": {
						"geoId": {
							"type": "string",
							"description": "The geoId of the hotel to search for"
						},
						"checkIn": {
							"type": "string",
							"format": "date",
							"description": "The check in date"
						},
						"checkOut": {
							"type": "string",
							"format": "date",
							"description": "The check out date"
						}
					},
					"required": [
						"geoId",
						"checkIn",
						"checkOut"
					]
				}
			}
		}
        return tool_call_format
