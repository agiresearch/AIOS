from pydantic import BaseModel, Field
from typing import List, Dict, Any, Union

class StorageQuery(BaseModel):
    messages: List[Dict[str, Union[str, Any]]]  # List of message dictionaries, each containing role and content.
    operation_type: str = Field(default="text")  # Type of the return message, default is "text".

    class Config:
        arbitrary_types_allowed = True  # Allows the use of arbitrary types such as Any and Dict.