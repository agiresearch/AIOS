from pydantic import BaseModel
from typing import List, Dict, Any, Union

class MemoryQuery(BaseModel):
    # messages: List[Dict[str, Union[str, Any]]]  # List of message dictionaries, each containing role and content.
    # message_return_type: str = Field(default="text")  # Type of the return message, default is "text".
    messages: List[Dict[str, Union[str, Any]]]
    operation_type: str

    class Config:
        arbitrary_types_allowed = True  # Allows the use of arbitrary types such as Any and Dict.
