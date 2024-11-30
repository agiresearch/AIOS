import os
import pytest
import requests
from requests.models import Response
import json

from pyopenagi.tools.imdb.top_series import TopSeries
from dotenv import load_dotenv, find_dotenv

@pytest.fixture(scope="module")
def test_rapid_api_key():
    load_dotenv(find_dotenv())
    if "RAPID_API_KEY" not in os.environ or not os.environ["RAPID_API_KEY"]:
        with pytest.raises(ValueError):
            TopSeries()
        pytest.skip("RAPID api key is not set.")
    else:
        return True

class ImdbTopSeriesMock:
    @staticmethod
    def json():
        mock_items = []
        mock_title = "Mock Title"
        mock_description = "Mock Description."
        mock_image = "https://m.media-amazon.com/images/Mock/Standard.Image.jpg"
        mock_big_image = "https://m.media-amazon.com/images/Mock/Big.Image.jpg"
        mock_genre = ["Drama", "Fantasy"]
        mock_thumbnail = "https://m.media-amazon.com/images/Mock/Thumb.Image.jpg"
        mock_rating = 9.2
        mock_year = "2011-2019"
        mock_imdbid = "tt0000000"
        mock_imdb_link = "https://www.imdb.com/title/tt0000000"

        for i in range(100):
            mock_items.append(
                {
                    "rank": i + 1,
                    "title": mock_title,
                    "description": mock_description,
                    "image": mock_image,
                    "big_image": mock_big_image,
                    "genre": mock_genre,
                    "thumbnail": mock_thumbnail,
                    "rating": mock_rating,
                    "id": f"top{i+1}",
                    "year": mock_year,
                    "imdbid": mock_imdbid,
                    "mock_imdb_link": mock_imdb_link,
                }
            )
        mock_response = Response()
        mock_response.status_code = 200
        mock_response._content = str.encode(json.dumps(mock_items))
        return mock_response.json()


@pytest.fixture(autouse=True)
def mock_response(monkeypatch):
    def mock_get(*args, **kwargs):
        return ImdbTopSeriesMock()

    monkeypatch.setattr(requests, "get", mock_get)


@pytest.mark.usefixtures("test_rapid_api_key")
@pytest.mark.parametrize(
    "valid_start, valid_end",
    [
        [1, 100],
        [60, 61],
        [60, 62],
    ],
)
def test_top_series_api_valid_input_outputs_valid_delimiter_count(
    valid_start, valid_end
):
    load_dotenv(find_dotenv())
    top_series_api = TopSeries()
    params = {"start": valid_start, "end": valid_end}
    result = top_series_api.run(params=params)
    assert isinstance(result, str)
    assert result.count(";") == max(0, int(valid_end) - int(valid_start))

@pytest.mark.usefixtures("test_rapid_api_key")
def test_top_series_api_reverse_range_returns_blank():
    load_dotenv(find_dotenv())
    top_series_api = TopSeries()
    params = {"start": 100, "end": 0}
    result = top_series_api.run(params=params)
    assert result == "Top 100-0 series ranked by IMDB are: "


@pytest.mark.parametrize(
    "invalid_start, valid_end",
    [
        ["0", 100],
        [0.5, 100],
        [[], 100],
        [{}, 100]
    ]
)
@pytest.mark.usefixtures("test_rapid_api_key")
def test_top_series_api_invalid_start_type_raises_typeerror(invalid_start, valid_end):
    load_dotenv(find_dotenv())
    top_series_api = TopSeries()
    params = {"start": invalid_start, "end": valid_end}
    with pytest.raises(TypeError):
        top_series_api.run(params=params)


@pytest.mark.parametrize(
    "invalid_start, valid_end",
    [
        [1, "0"],
        [1, 0.5],
        [1, []],
        [1, {}]
    ]
)
@pytest.mark.usefixtures("test_rapid_api_key")
def test_top_series_api_invalid_end_type_raises_typeerror(invalid_start, valid_end):
    load_dotenv(find_dotenv())
    top_series_api = TopSeries()
    params = {"start": invalid_start, "end": valid_end}
    with pytest.raises(TypeError):
        top_series_api.run(params=params)

@pytest.mark.usefixtures("test_rapid_api_key")
def test_top_series_api_invalid_start_count_raises_indexerror():
    load_dotenv(find_dotenv())
    top_series_api = TopSeries()
    invalid_start = {"start": 101, "end": 102}
    with pytest.raises(IndexError):
        top_series_api.run(params=invalid_start)

@pytest.mark.usefixtures("test_rapid_api_key")
def test_top_series_api_invalid_end_count_raises_indexerror():
    load_dotenv(find_dotenv())
    top_series_api = TopSeries()
    invalid_end = {"start": 1, "end": 101}
    with pytest.raises(IndexError):
        top_series_api.run(params=invalid_end)
