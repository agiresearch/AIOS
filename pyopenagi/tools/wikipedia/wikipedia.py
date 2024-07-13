from ..base import BaseTool
# from langchain_core.documents import Document
from typing import Optional, Any, Dict
class Wikipedia(BaseTool):
    """Wikipedia tool, refactored from langchain.

    To use, you should have the ``wikipedia`` python package installed.
    This wrapper will use the Wikipedia API to conduct searches and
    fetch page summaries. By default, it will return the page summaries
    of the top-k results.
    It limits the Document content by doc_content_chars_max.
    """
    def __init__(self):
        super().__init__()
        self.WIKIPEDIA_MAX_QUERY_LENGTH = 300
        self.top_k_results = 3
        self.lang = "en"
        self.load_all_available_meta: bool = False
        self.doc_content_chars_max: int = 4000
        self.wiki_client = self.build_client()

    def build_client(self):
        try:
            import pyopenagi.tools.wikipedia.wikipedia as wikipedia

            wikipedia.set_lang(self.lang)

        except ImportError:
            raise ImportError(
                "Could not import wikipedia python package. "
                "Please install it with `pip install wikipedia`."
            )
        return wikipedia

    def run(self, query: Dict[str, str]) -> str:
        """Run Wikipedia search and get page summaries."""
        if not isinstance(query, dict) or 'query' not in query:
            raise TypeError("Query must be a dictionary with a 'query' key")
        query_str = query['query'][:self.WIKIPEDIA_MAX_QUERY_LENGTH]  # Extract and slice the query string
        page_titles = self.wiki_client.search(query_str, results=self.top_k_results)
        summaries = []
        for page_title in page_titles[: self.top_k_results]:
            if wiki_page := self._fetch_page(page_title):
                if summary := self._formatted_page_summary(page_title, wiki_page):
                    summaries.append(summary)
        if not summaries:
            return "No good Wikipedia Search Result was found"
        return "\n\n".join(summaries)[: self.doc_content_chars_max]

    @staticmethod
    def _formatted_page_summary(page_title: str, wiki_page: Any) -> Optional[str]:
        return f"Page: {page_title}\nSummary: {wiki_page.summary}"

    def get_tool_call_format(self):
        tool_call_format = {
			"type": "function",
			"function": {
				"name": "wikipedia",
				"description": "Provides relevant information about the destination",
				"parameters": {
					"type": "object",
					"properties": {
						"query": {
							"type": "string",
							"description": "Search query for Wikipedia"
						}
					},
					"required": [
						"query"
					]
				}
			}
		}
        return tool_call_format
