from ..base import BaseRapidAPITool

from pyopenagi.utils.utils import get_from_env

import requests

import json

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
                "classOfService": params["classOfService"],
                "returnDate": params["returnDate"]
            }
        except ValueError:
            raise KeyError(
                "The keys in params do not match the excepted keys in params for tripadvisor search flight api. "
                "Please make sure it contains following required keys: "
                "sourceAirportCode",
                "destinationAirportCode",
                "itineraryType",
                "sortOrder",
                "classOfService",
                "returnDate",
                "date"
            )

        response = requests.get(self.url, headers=headers, params=self.query_string).json()
        return self.parse_result(response)

    def parse_result(self, response) -> str:
        # Accessing the 'flights' data from within the 'data' key
        if 'data' in response and 'flights' in response['data']:
            flights_data = response['data']['flights']
            simplified_results = []
            flight_count = 0
            for flight in flights_data:
                if flight_count >= 2:
                    break
                for segment in flight['segments']:
                    for leg in segment['legs']:
                        simplified_result = {
                            'originStationCode': leg['originStationCode'],
                            'destinationStationCode': leg['destinationStationCode'],
                            'departureDateTime': leg['departureDateTime'],
                            'arrivalDateTime': leg['arrivalDateTime'],
                            'classOfService': leg['classOfService'],
                            'marketingCarrierCode': leg['marketingCarrierCode'],
                            'operatingCarrierCode': leg['operatingCarrierCode'],
                            'flightNumber': leg['flightNumber'],
                            'numStops': leg['numStops'],
                            'distanceInKM': leg['distanceInKM'],
                            'isInternational': leg['isInternational']
                        }
                        simplified_results.append(simplified_result)
                flight_count += 1
            return json.dumps(simplified_results)
        else:
            return json.dumps([])

    def get_tool_call_format(self):
        tool_call_format = {
			"type": "function",
			"function": {
				"name": "flight_search",
				"description": "Provides details about a flight",
				"parameters": {
					"type": "object",
					"properties": {
						"sourceAirportCode": {
							"type": "string",
							"description": "The source airport code of the flight to search for"
						},
						"date": {
							"type": "string",
							"format": "date",
							"description": "The date of the flight"
						},
						"returnDate": {
							"type": "string",
							"format": "date",
							"description": "The return date of the flight"
						},
						"destinationAirportCode": {
							"type": "string",
							"description": "The destination airport code of the flight"
						},
						"itineraryType": {
							"type": "string",
							"enum": [
								"ONE_WAY",
								"ROUND_TRIP"
							],
							"description": "The type of itinerary"
						},
						"sortOrder": {
							"type": "string",
							"enum": [
								"ML_BEST_VALUE",
								"DURATION",
								"PRICE",
								"EARLIEST_OUTBOUND_DEPARTURE",
								"EARLIEST_OUTBOUND_ARRIVAL",
								"LATEST_OUTBOUND_DEPARTURE",
								"LATEST_OUTBOUND_ARRIVAL"
							],
							"description": "The order to sort the results"
						},
						"classOfService": {
							"type": "string",
							"enum": [
								"ECONOMY",
								"PREMIUM_ECONOMY",
								"BUSINESS",
								"FIRST"
							],
							"description": "The class of service for the flight"
						},
						"numSeniors": {
							"type": "number",
							"description": "The number of seniors in the itinerary"
						},
						"numAdults": {
							"type": "number",
							"description": "The number of adults in the itinerary"
						}
					},
					"required": [
						"sourceAirportCode",
						"date",
						"destinationAirportCode",
						"itineraryType",
						"sortOrder",
						"classOfService",
						"numSeniors",
						"numAdults",
						"returnDate"
					]
				}
			}
		}
        return tool_call_format
