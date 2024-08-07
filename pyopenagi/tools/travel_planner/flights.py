import pandas as pd
import os
from pandas import DataFrame

from ..base import BaseTool


class Flights(BaseTool):

    def __init__(self, path="../../environments/travelPlanner/flights/clean_Flights_2022.csv"):
        current_dir = os.path.dirname(os.path.abspath(__file__))
        self.path = os.path.join(current_dir, path)
        self.data = pd.read_csv(self.path).dropna()[
            ['Flight Number', 'Price', 'DepTime', 'ArrTime', 'ActualElapsedTime', 'FlightDate', 'OriginCityName',
             'DestCityName', 'Distance']]
        print("Flights loaded.")

    def load_db(self):
        self.data = pd.read_csv(self.path).dropna().rename(columns={'Unnamed: 0': 'Flight Number'})

    def run(self,
            origin: str,
            destination: str,
            departure_date: str,
            ) -> DataFrame:
        """Search for flights by origin, destination, and departure date."""
        results = self.data[self.data["OriginCityName"] == origin]
        results = results[results["DestCityName"] == destination]
        results = results[results["FlightDate"] == departure_date]

        if len(results) == 0:
            return "There is no flight from {} to {} on {}.".format(origin, destination, departure_date)
        return results

    def get_tool_call_format(self):
        tool_call_format = {
            "type": "function",
            "function": {
                "name": "Flights",
                "description": "Search for Flights by query",
            }
        }
        return tool_call_format
