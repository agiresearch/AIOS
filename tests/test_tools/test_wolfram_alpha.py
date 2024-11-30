import os
import pytest

from pyopenagi.tools.wolfram.wolfram_alpha import WolframAlpha
from dotenv import load_dotenv, find_dotenv

@pytest.fixture(scope="module")
def test_wolfram_alpha_id():
    load_dotenv(find_dotenv())
    if "WOLFRAM_ALPHA_APPID" not in os.environ or not os.environ["WOLFRAM_ALPHA_APPID"]:
        with pytest.raises(ValueError):
            WolframAlpha()
        pytest.skip("WolframAlpha app id is not set.")
    else:
        return True

@pytest.mark.usefixtures("test_wolfram_alpha_id")
def test_wolfram_alpha():
    wolfram_alpha = WolframAlpha()
    query = "What is the square root of 144?"
    result = wolfram_alpha.run(query)
    assert "12" in result
