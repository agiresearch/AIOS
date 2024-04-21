from ...base import BaseRapidAPITool

from typing import Any, Dict, List, Optional

from src.utils.utils import get_from_env

import requests

import os

import json

class RestaurantLocationSearch(BaseRapidAPITool):
    def __init__(self):
        super().__init__()
        self.url = "https://tripadvisor16.p.rapidapi.com/api/v1/restaurant/searchLocation"
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
                "The keys in params do not match the excepted keys in params for tripadvisor search restaurant location api. "
                "Please make sure it contains the key: 'query'"
            )

        # print(self.query_string)

        response = requests.get(self.url, headers=headers, params=self.query_string).json()

        return json.dumps(response)

    def parse_result(self, response) -> str:
        raise NotImplementedError


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
                "locationId": params["locationID"]
            }
        except ValueError:
            raise KeyError(
                "The keys in params do not match the excepted keys in params for tripadvisor search restaurant api. "
                "Please make sure it contains following required keys: "
                "locationID",
            )

        response = requests.get(self.url, headers=headers, params=self.query_string).json()
        return json.dumps(response)


    def parse_result(self, response) -> str:
        raise NotImplementedError


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
                "restaurantsID": params["restaurantsID"],
            }
        except ValueError:
            raise KeyError(
                "The keys in params do not match the excepted keys in params for tripadvisor get restaurant details api. "
                "Please make sure it contains the key: 'restaurantsID'"
            )

        response = requests.get(self.url, headers=headers, params=self.query_string).json()
        return json.dumps(response)


    def parse_result(self, response) -> str:
        raise NotImplementedError
