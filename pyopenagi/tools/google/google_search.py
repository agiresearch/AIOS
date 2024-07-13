from ..base import BaseTool

from pyopenagi.utils.utils import get_from_env

from typing import List, Any

class GoogleSearch(BaseTool):
    """Google Search Tool, refactored from langchain.

    Adapted from: Instructions adapted from https://stackoverflow.com/questions/
    37083058/
    programmatically-searching-google-in-python-using-custom-search

    1. Install google-api-python-client
    - If you don't already have a Google account, sign up.
    - If you have never created a Google APIs Console project,
    read the Managing Projects page and create a project in the Google API Console.
    - Install the library using pip install google-api-python-client

    2. Enable the Custom Search API
    - Navigate to the APIs & Services→Dashboard panel in Cloud Console.
    - Click Enable APIs and Services.
    - Search for Custom Search API and click on it.
    - Click Enable.
    URL for it: https://console.cloud.google.com/apis/library/customsearch.googleapis
    .com

    3. To create an API key:
    - Navigate to the APIs & Services → Credentials panel in Cloud Console.
    - Select Create credentials, then select API key from the drop-down menu.
    - The API key created dialog box displays your newly created key.
    - You now have an API_KEY

    Alternatively, you can just generate an API key here:
    https://developers.google.com/custom-search/docs/paid_element#api_key

    4. Setup Custom Search Engine so you can search the entire web
    - Create a custom search engine here: https://programmablesearchengine.google.com/.
    - In `What to search` to search, pick the `Search the entire Web` option.
    After search engine is created, you can click on it and find `Search engine ID`
      on the Overview page.

    """
    def __init__(self):
        super().__init__()
        self.google_api_key = get_from_env("GOOGLE_API_KEY")
        self.google_cse_id = get_from_env("GOOGLE_CSE_ID")
        self.k: int = 10 # topk searched results
        self.search_engine = self.build_engine()
        self.siterestrict: bool = False

    def build_engine(self):
        try:
            from googleapiclient.discovery import build

        except ImportError:
            raise ImportError(
                "google-api-python-client is not installed. "
                "Please install it with `pip install google-api-python-client"
                ">=2.100.0`"
            )
        engine = build("customsearch", "v1", developerKey=self.google_api_key)
        return engine

    def _google_search_results(self, search_term: str, **kwargs: Any) -> List[dict]:
        cse = self.search_engine.cse()
        if self.siterestrict:
            cse = cse.siterestrict() # TODO add siterestrict verification
        res = cse.list(q=search_term, cx=self.google_cse_id, **kwargs).execute()
        return res.get("items", [])


    def run(self, query: str) -> str:
        """Run query through GoogleSearch and parse result."""
        response = self._google_search_results(query, num=self.k)
        result = self.parse_result(response)
        return result

    def parse_result(self, response):
        snippets = []
        if len(response) == 0:
            return "No good Google Search Result was found"
        for result in response:
            if "snippet" in result:
                snippets.append(result["snippet"])

        return " ".join(snippets)
