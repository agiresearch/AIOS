import requests

from ..base import BaseTool

from typing import List
# from pydantic import root_validator

from pyopenagi.utils.utils import get_from_env

class BingSearch(BaseTool):
    """Bing Search Tool, refactored from langchain.
    In order to set this up, follow instructions at:
    https://levelup.gitconnected.com/api-tutorial-how-to-use-bing-web-search-api-in-python-4165d5592a7e
    """
    def __init__(self):
        super().__init__()
        self.url = "https://api.bing.microsoft.com/v7.0/search" # temporarily
        self.bing_subscription_key = get_from_env("BING_SUBSCRIPTION_KEY")
        self.k: int = 10 # topk searched results
        # search_kwargs: dict

    def _bing_search_results(self, search_term: str, count: int) -> List[dict]:
        headers = {"Ocp-Apim-Subscription-Key": self.bing_subscription_key}
        params = {
            "q": search_term,
            "count": count,
            "textDecorations": True,
            "textFormat": "HTML",
            # **self.search_kwargs,
        }
        response = requests.get(
            self.bing_search_url,
            headers=headers,
            params=params,  # type: ignore
        )
        response.raise_for_status()
        search_results = response.json()
        if "webPages" in search_results:
            return search_results["webPages"]["value"]
        return []

    def run(self, query: str) -> str:
        """Run query through BingSearch and parse result."""
        response = self._bing_search_results(query, count=self.k)
        result = self.parse_result(response)
        return result

    def parse_result(self, response):
        snippets = []
        if len(response) == 0:
            return "No good Bing Search Result was found"
        for result in response:
            snippets.append(result["snippet"])

        return " ".join(snippets)
