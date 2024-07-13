from ..base import BaseTool

from pyopenagi.utils.utils import get_from_env
class WolframAlpha(BaseTool):
    """Wolfram Alpha Tool, refactored from langchain.

    Docs for using:

    1. Go to wolfram alpha and sign up for a developer account
    2. Create an app and get your APP ID
    3. Save your APP ID into WOLFRAM_ALPHA_APPID env variable
    4. pip install wolframalpha

    """
    def __init__(self):
        super().__init__()
        self.wolfram_alpha_appid = get_from_env("WOLFRAM_ALPHA_APPID")
        self.wolfram_client = self.build_client()

    def build_client(self):
        try:
            import wolframalpha

        except ImportError:
            raise ImportError(
                "wolframalpha is not installed. "
                "Please install it with `pip install wolframalpha`"
            )
        client = wolframalpha.Client(self.wolfram_alpha_appid)
        return client

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


    def get_tool_call_format(self):
        tool_call_format = {
            "type": "function",
            "function": {
                "name": "wolfram_alpha",
                "description": "Use specific mathematical knowledge (algebra, calculus, geometry, etc) to answer the given query",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "the abstracted mathematical query that needs to be answered"
                        }
                    },
                    "required": [
                        "query"
                    ]
                }
            }
        }
        return tool_call_format
