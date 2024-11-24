from pydantic import BaseModel
from typing import List, Dict, Any, Union

class ToolQuery(BaseModel):
    tool_calls: List[Dict[str, Union[str, Any]]]  # List of message dictionaries, each containing role and content.

    class Config:
        arbitrary_types_allowed = True  # Allows the use of arbitrary types such as Any and Dict.

