import os

from ..base import BaseTool


class Cities(BaseTool):
    def __init__(self, path="../../environments/travelPlanner/background/citySet_with_states.txt") -> None:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        self.path = os.path.join(current_dir, path)
        self.load_data()
        print("Cities loaded.")

    def load_data(self):
        cityStateMapping = open(self.path, "r").read().strip().split("\n")
        self.data = {}
        for unit in cityStateMapping:
            city, state = unit.split("\t")
            if state not in self.data:
                self.data[state] = [city]
            else:
                self.data[state].append(city)

    def run(self, state) -> dict:
        if state not in self.data:
            return ValueError("Invalid State")
        else:
            return self.data[state]

    def get_tool_call_format(self):
        tool_call_format = {
            "type": "function",
            "function": {
                "name": "Cities",
                "description": "Search for Cities by query",
            }
        }
        return tool_call_format
