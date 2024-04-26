from ...base import BaseRapidAPITool

from typing import Any, Dict, List, Optional

from src.utils.utils import get_from_env

import requests

import os

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
        return json.dumps(response)

        # result = self.parse_result(response)
        # return result

    # def parse_result(self, response) -> str:
    #     airports = []
    #     for d in response["data"]:
    #         print(d)
    #         airports.append(f"{d["name"]}, airport code is {d["airportCode"]}")

    #     return "Available airports are " + ";".join(airports)

class FlightSearch(BaseRapidAPITool):
    def __init__(self):
        super().__init__()
        self.url = "https://tripadvisor16.p.rapidapi.com/api/v1/flights/searchFlights"
        self.host_name = "tripadvisor16.p.rapidapi.com"
        self.api_key = get_from_env("RAPID_API_KEY")

    def run(self, params: dict):
        headers = {
            "X-RapidAPI-Key": self.api_key,
            "X-RapidAPI-Host": self.host_name
        }

        try:
            self.query_string = {
                "sourceAirportCode": params["sourceAirportCode"],
                "date": params["date"],
                "destinationAirportCode": params["destinationAirportCode"],
                "itineraryType": params["itineraryType"],
                "sortOrder": params["sortOrder"],
                "classOfService": params["classOfService"]
            }
        except ValueError:
            raise KeyError(
                "The keys in params do not match the excepted keys in params for tripadvisor search flight api. "
                "Please make sure it contains following required keys: "
                "sourceAirportCode",
                "destinationAirport",
                "itineraryType",
                "sortOrder",
                "classOfServices"
            )

        response = requests.get(self.url, headers=headers, params=self.query_string).json()
        return json.dumps(response)


    def parse_result(self, response) -> str:
        raise NotImplementedError
