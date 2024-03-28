from typing import Any, Dict, Optional

from src.tools.base import BaseTool

# import wolfram_alpha

from pydantic import root_validator

class WolframAlpha(BaseTool):
    """Wrapper for Wolfram Alpha.

    Docs for using:

    1. Go to wolfram alpha and sign up for a developer account
    2. Create an app and get your APP ID
    3. Save your APP ID into WOLFRAM_ALPHA_APPID env variable
    4. pip install wolframalpha

    """

    wolfram_client: Any  #: :meta private:
    wolfram_alpha_appid: Optional[str] = None

    @root_validator(pre=True)
    def validate_environment(cls, values: Dict) -> Dict:
        """Validate that the python package exists in environment."""
        try:
            import tools.online.arxiv as arxiv

            values["arxiv_search"] = arxiv.Search
            values["arxiv_exceptions"] = (
                arxiv.ArxivError,
                arxiv.UnexpectedEmptyPageError,
                arxiv.HTTPError,
            )
            values["arxiv_result"] = arxiv.Result
        except ImportError:
            raise ImportError(
                "Could not import arxiv python package. "
                "Please install it with `pip install arxiv`."
            )
        return values


    def run(self, query: str) -> str:
        """Run query through WolframAlpha and parse result."""
        res = self.wolfram_client.query(query)

        try:
            assumption = next(res.pods).text
            answer = next(res.results).text
        except StopIteration:
            return "Wolfram Alpha wasn't able to answer it"

        if answer is None or answer == "":
            # We don't want to return the assumption alone if answer is empty
            return "No good Wolfram Alpha Result was found"
        else:
            return f"Assumption: {assumption} \nAnswer: {answer}"