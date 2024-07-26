import pandas as pd
import os
from pandas import DataFrame


class Attractions:
    def __init__(self, path="../../environments/travelPlanner/attractions/attractions.csv"):
        current_dir = os.path.dirname(os.path.abspath(__file__))
        self.path = os.path.join(current_dir, path)
        self.data = pd.read_csv(self.path).dropna()[['Name','Latitude','Longitude','Address','Phone','Website',"City"]]
        print("Attractions loaded.")

    def load_db(self):
        self.data = pd.read_csv(self.path)

    def run(self,
            city: str,
            ) -> DataFrame:
        """Search for Accommodations by city and date."""
        results = self.data[self.data["City"] == city]
        # the results should show the index
        results = results.reset_index(drop=True)
        if len(results) == 0:
            return "There is no attraction in this city."
        return results  
    
    def get_tool_call_format(self):
        pass