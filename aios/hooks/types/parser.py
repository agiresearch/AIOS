from pydantic import BaseModel
from typing import Any

class ParserQuery(BaseModel):
    name: str
    message: str
    system_message: str | None = None
    temperature: float = 0.3
    max_tokens: float | None = None
    json: bool = False
    schema: Any | None = None