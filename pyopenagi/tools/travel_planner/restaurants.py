import pandas as pd
from pandas import DataFrame

class Restaurants:
    def __init__(self, path="../environment/database/restaurants/clean_restaurant_2022.csv"):
        self.path = path
        self.data = pd.read_csv(self.path).dropna()[['Name','Average Cost','Cuisines','Aggregate Rating','City']]
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
