import pandas as pd
import os
from pandas import DataFrame

from ..base import BaseTool


class Restaurants(BaseTool):
    def __init__(self, path="../../environments/travelPlanner/restaurants/clean_restaurant_2022.csv"):
        super().__init__()
        current_dir = os.path.dirname(os.path.abspath(__file__))
        self.path = os.path.join(current_dir, path)
        self.data = pd.read_csv(self.path).dropna()[['Name', 'Average Cost', 'Cuisines', 'Aggregate Rating', 'City']]
        print("Restaurants loaded.")

    def load_db(self):
        self.data = pd.read_csv(self.path).dropna()

    def run(self,
            city: str,
            ) -> DataFrame:
        """Search for restaurant ."""
        results = self.data[self.data["City"] == city]

        if len(results) == 0:
            return "There is no restaurant in this city."
        return results

    def get_tool_call_format(self):
        tool_call_format = {
            "type": "function",
            "function": {
                "name": "Restaurants",
                "description": "Search for Restaurants by query",
            }
        }
        return tool_call_format
