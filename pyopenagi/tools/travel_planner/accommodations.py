import pandas as pd
import os
from pandas import DataFrame

from ..base import BaseTool


class Accommodations(BaseTool):
    def __init__(self, path="../../environments/travelPlanner/accommodations/clean_accommodations_2022.csv"):
        current_dir = os.path.dirname(os.path.abspath(__file__))
        self.path = os.path.join(current_dir, path)
        self.data = pd.read_csv(self.path).dropna()[
            ['NAME', 'price', 'room type', 'house_rules', 'minimum nights', 'maximum occupancy', 'review rate number',
             'city']]
        print("Accommodations loaded.")

    def load_db(self):
        self.data = pd.read_csv(self.path).dropna()

    def run(self,
            city: str,
            ) -> DataFrame:
        """Search for accommodations by city."""
        results = self.data[self.data["city"] == city]
        if len(results) == 0:
            return "There is no attraction in this city."

        return results

    def get_tool_call_format(self):
        tool_call_format = {
            "type": "function",
            "function": {
                "name": "Accommodations",
                "description": "Search for an Accommodations by query",
            }
        }
        return tool_call_format
