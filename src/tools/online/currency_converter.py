from ..base import BaseRapidAPITool

from typing import Any, Dict, List, Optional

# from pydantic import root_validator

from src.utils.utils import get_from_env

import requests

import os

class CurrencyConverterAPI(BaseRapidAPITool):
    def __init__(self):
        super().__init__()
        self.url = "https://currency-converter5.p.rapidapi.com/currency/convert"
        self.host_name = "currency-converter5.p.rapidapi.com"
        self.api_key = get_from_env("RAPID_API_KEY")

    def run(self, params: dict):
        headers = {
            "X-RapidAPI-Key": self.api_key,
            "X-RapidAPI-Host": self.host_name
        }
        try:
            self.query_string = {
                "from": params["from"],
                "to": params["to"],
                "amount": params["amount"]
            }
        except ValueError:
            raise KeyError(
                "The keys in params do not match the excepted keys in params for currency converter api. "
                "Please make sure it contains two keys: 'from' and 'to' and 'amount"
            )

        # print(self.query_string)

        response = requests.get(self.url, headers=headers, params=self.query_string).json()

        result = self.parse_result(response)
        return result

    def parse_result(self, response) -> str:
        results = []
        amount = str(response["amount"])
        base = response["base_currency_name"]
        rates = response["rates"]

        for key, value in rates.items():
            converted = value["currency_name"]
            converted_rate = value["rate"]
            converted_amount = value["rate_for_amount"]
            results.append("Currency from " + base + " to " + converted + "is " + converted_rate + ".", )
            results.append(amount + " " + base + "can be converted to " + converted_amount + " " + converted + ".")

        return " ".join(results)
