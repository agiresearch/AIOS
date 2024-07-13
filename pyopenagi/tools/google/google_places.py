import logging
from typing import Any, Dict, Optional

from ..base import BaseTool

from pyopenagi.utils.utils import get_from_env


class GooglePlaces(BaseTool):
    """Google Places API, refactored from langchain.

    To use, you should have the ``googlemaps`` python package installed,
     **an API key for the google maps platform**,
     and the environment variable ''GPLACES_API_KEY''
     set with your API key , or pass 'gplaces_api_key'
     as a named parameter to the constructor.

    By default, this will return the all the results on the input query.
     You can use the top_k_results argument to limit the number of results.

    Example:
        .. code-block:: python


            from langchain_community.utilities import GooglePlacesAPIWrapper
            gplaceapi = GooglePlacesAPIWrapper()
    """
    def __init__(self):
        super().__init__()
        self.gplaces_api_key = get_from_env("GPLACES_API_KEY")
        self.google_map_client: Any  #: :meta private:
        self.top_k_results: Optional[int] = None

    def build_client(self):
        """Validate that api key is in your environment variable."""
        try:
            import googlemaps

            client = googlemaps.Client(self.gplaces_api_key)
        except ImportError:
            raise ImportError(
                "Could not import googlemaps python package. "
                "Please install it with `pip install googlemaps`."
            )
        return client

    def run(self, query: str) -> str:
        """Run Places search and get k number of places that exists that match."""
        search_results = self.google_map_client.places(query)["results"]
        num_to_return = len(search_results)

        places = []

        if num_to_return == 0:
            return "Google Places did not find any places that match the description"

        num_to_return = (
            num_to_return
            if self.top_k_results is None
            else min(num_to_return, self.top_k_results)
        )

        for i in range(num_to_return):
            result = search_results[i]
            details = self.fetch_place_details(result["place_id"])

            if details is not None:
                places.append(details)

        return "\n".join([f"{i+1}. {item}" for i, item in enumerate(places)])

    def fetch_place_details(self, place_id: str) -> Optional[str]:
        try:
            place_details = self.google_map_client.place(place_id)
            place_details["place_id"] = place_id
            formatted_details = self.format_place_details(place_details)
            return formatted_details
        except Exception as e:
            logging.error(f"An Error occurred while fetching place details: {e}")
            return None

    def format_place_details(self, place_details: Dict[str, Any]) -> Optional[str]:
        try:
            name = place_details.get("result", {}).get("name", "Unknown")
            address = place_details.get("result", {}).get(
                "formatted_address", "Unknown"
            )
            phone_number = place_details.get("result", {}).get(
                "formatted_phone_number", "Unknown"
            )
            website = place_details.get("result", {}).get("website", "Unknown")
            place_id = place_details.get("result", {}).get("place_id", "Unknown")

            formatted_details = (
                f"{name}\nAddress: {address}\n"
                f"Google place ID: {place_id}\n"
                f"Phone: {phone_number}\nWebsite: {website}\n\n"
            )
            return formatted_details
        except Exception as e:
            logging.error(f"An error occurred while formatting place details: {e}")
            return None
