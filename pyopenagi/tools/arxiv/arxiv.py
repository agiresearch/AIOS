import re

from ..base import BaseTool

import arxiv

from typing import Optional

class Arxiv(BaseTool):
    """Arxiv Tool, refactored from Langchain.

    To use, you should have the ``arxiv`` python package installed.
    https://lukasschwab.me/arxiv.py/index.html
    This wrapper will use the Arxiv API to conduct searches and
    fetch document summaries. By default, it will return the document summaries
    of the top-k results.
    If the query is in the form of arxiv identifier
    (see https://info.arxiv.org/help/find/index.html), it will return the paper
    corresponding to the arxiv identifier.
    It limits the Document content by doc_content_chars_max.
    Set doc_content_chars_max=None if you don't want to limit the content size.

    Attributes:
        top_k_results: number of the top-scored document used for the arxiv tool
        ARXIV_MAX_QUERY_LENGTH: the cut limit on the query used for the arxiv tool.
        load_max_docs: a limit to the number of loaded documents
        load_all_available_meta:
            if True: the `metadata` of the loaded Documents contains all available
            meta info (see https://lukasschwab.me/arxiv.py/index.html#Result),
            if False: the `metadata` contains only the published date, title,
            authors and summary.
        doc_content_chars_max: an optional cut limit for the length of a document's
            content
    """

    def __init__(self):
        super().__init__()
        self.top_k_results: int = 3
        self.ARXIV_MAX_QUERY_LENGTH: int = 300
        self.load_max_docs: int = 100
        self.load_all_available_meta: bool = False
        self.doc_content_chars_max: Optional[int] = 4000
        self.build_client()

    def is_arxiv_identifier(self, query: str) -> bool:
        """Check if a query is an arxiv identifier."""
        arxiv_identifier_pattern = r"\d{2}(0[1-9]|1[0-2])\.\d{4,5}(v\d+|)|\d{7}.*"
        for query_item in query[: self.ARXIV_MAX_QUERY_LENGTH].split():
            match_result = re.match(arxiv_identifier_pattern, query_item)
            if not match_result:
                return False
            assert match_result is not None
            if not match_result.group(0) == query_item:
                return False
        return True

    def build_client(self):
        """Validate that the python package exists in environment."""
        self.arxiv_search = arxiv.Search
        self.arxiv_exceptions = arxiv.ArxivError

    def run(self, params) -> str:
        """
        Performs an arxiv search and A single string
        with the publish date, title, authors, and summary
        for each article separated by two newlines.

        If an error occurs or no documents found, error text
        is returned instead. Wrapper for
        https://lukasschwab.me/arxiv.py/index.html#Search

        Args:
            query: a plaintext search query
        """  # noqa: E501
        query = params["query"]
        try:
            if self.is_arxiv_identifier(query):
                results = self.arxiv_search(
                    id_list=query.split(),
                    max_results=self.top_k_results,
                ).results()
            else:
                results = self.arxiv_search(  # type: ignore
                    query[: self.ARXIV_MAX_QUERY_LENGTH], max_results=self.top_k_results
                ).results()
        except self.arxiv_exceptions as ex:
            return f"Arxiv exception: {ex}"
        docs = [
            f"Published: {result.updated.date()}\n"
            f"Title: {result.title}\n"
            f"Authors: {', '.join(a.name for a in result.authors)}\n"
            f"Summary: {result.summary}"
            for result in results
        ]
        if docs:
            return "\n\n".join(docs)[: self.doc_content_chars_max]
        else:
            return "No good Arxiv Result was found"

    def get_tool_call_format(self):
        tool_call_format = {
            "type": "function",
            "function": {
                "name": "arxiv",
                "description": "Query articles or topics in arxiv",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Input query that describes what to search in arxiv"
                        }
                    },
                    "required": [
                        "query"
                    ]
                }
            }
        }
        return tool_call_format
