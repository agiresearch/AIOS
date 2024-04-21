from ...base import BaseRapidAPITool

from typing import Any, Dict, List, Optional

from src.utils.utils import get_from_env

import requests

import os

import json

class HotelLocationSearch(BaseRapidAPITool):
    def __init__(self):
        super().__init__()
        self.url = "https://tripadvisor16.p.rapidapi.com/api/v1/hotels/searchLocation"
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
                "The keys in params do not match the excepted keys in params for tripadvisor search hotel location api. "
                "Please make sure it contains the key: 'query'"
            )

        # print(self.query_string)

        response = requests.get(self.url, headers=headers, params=self.query_string).json()

        return json.dumps(response)

    def parse_result(self, response) -> str:
        raise NotImplementedError

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
                "geoID": params["geoID"],
                "checkIn": params["checkIn"],
                "checkOut": params["checkOut"],
            }
        except ValueError:
            raise KeyError(
                "The keys in params do not match the excepted keys in params for tripadvisor search hotel api. "
                "Please make sure it contains following required keys: "
                "geoID",
                "checkIn",
                "checkOut",
            )

        response = requests.get(self.url, headers=headers, params=self.query_string).json()
        return json.dumps(response)


    def parse_result(self, response) -> str:
        raise NotImplementedError

class GetHotelDetails(BaseRapidAPITool):
    def __init__(self):
        super().__init__()
        self.url = "https://tripadvisor16.p.rapidapi.com/api/v1/hotels/getHotelDetails"
        self.host_name = "tripadvisor16.p.rapidapi.com"
        self.api_key = get_from_env("RAPID_API_KEY")

    def run(self, params: dict):
        headers = {
            "X-RapidAPI-Key": self.api_key,
            "X-RapidAPI-Host": self.host_name
        }

        try:
            self.query_string = {
                "id": params["id"],
                "checkIn": params["checkIn"],
                "checkOut": params["checkOut"],
            }
        except ValueError:
            raise KeyError(
                "The keys in params do not match the excepted keys in params for tripadvisor get hotel details api. "
                "Please make sure it contains following required keys: "
                "id",
                "checkIn",
                "checkOut",
            )

        response = requests.get(self.url, headers=headers, params=self.query_string).json()
        return json.dumps(response)


    def parse_result(self, response) -> str:
        raise NotImplementedError
