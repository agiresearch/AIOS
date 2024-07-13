from ..base import BaseRapidAPITool

from pyopenagi.utils.utils import get_from_env

import requests

class CurrencyConverter(BaseRapidAPITool):
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
                "amount": params["amount"] if "amount" in params else "1.0"
            }
        except ValueError:
            raise KeyError(
                "The keys in params do not match the excepted keys in params for currency converter api. "
                "Please make sure it contains two keys: 'from' and 'to'"
            )

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

    def get_tool_call_format(self):
        tool_call_format = {
            "type": "function",
            "function": {
                "name": "currency_converter",
                "description": "Provides currency exchange rates convert base currency to desired currency with the given amount",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "from": {
                            "type": "string",
                            "description": "Base currency code, e.g., AUD, CAD, EUR, GBP..."
                        },
                        "to": {
                            "type": "string",
                            "description": "Desired currency code, e.g., AUD, CAD, EUR, GBP..."
                        },
                        "amount": {
                            "type": "string",
                            "default": "1.0",
                            "description": "The amount to be converted"
                        }
                    },
                    "required": [
                        "from",
                        "to"
                    ]
                }
            }
        }
        return tool_call_format
