import os

from src.tools.online.google_search import GoogleSearch

from src.tools.online.wolfram_alpha import WolframAlpha

from src.tools.online.words_api import WordsAPI

from src.tools.online.currency_converter import CurrencyConverterAPI

import pytest

from src.utils.utils import get_from_env

# def test_words_api():
#     if "RAPID_API_KEY" not in os.environ or not os.environ["RAPID_API_KEY"]:
#         with pytest.raises(ValueError):
#             words_api = WordsAPI()

#     else:
#         words_api = WordsAPI()
#         with pytest.raises(KeyError):
#             params = {
#                 "w": "hatchback",
#                 "api_name": "typeOf"
#             }
#             result = words_api.run(params=params)

#         params = {
#             "word": "hatchback",
#             "api_name": "typeOf"
#         }
#         result = words_api.run(params=params)
#         assert isinstance(result, str)


def test_currency_converter_api():
    if "RAPID_API_KEY" not in os.environ or not os.environ["RAPID_API_KEY"]:
        with pytest.raises(ValueError):
            currency_converter_api = CurrencyConverterAPI()
    else:
        currency_converter_api = CurrencyConverterAPI()
        with pytest.raises(KeyError):
            params = {
                "from x": "USD",
                "to": "EUR",
                "amount": 2
            }
            result = currency_converter_api.run(params=params)

        params = {
            "from": "USD",
            "to": "EUR",
            "amount": 2
        }
        result = currency_converter_api.run(params=params)
        # print(result)
        assert isinstance(result, str)
