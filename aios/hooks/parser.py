from aios.core.types import _obj, array, string, integer, _float
from aios.core.schema import CoreSchema
from aios.core import complete

def useCompletion():
    """
    Wrapper for internal complete function
    """

    def _(
        name: str,
        message: str,
        system_message: str | None = None,
        temperature: float = 0.3,
        max_tokens: float | None = None,
        json: bool = False,
        schema: CoreSchema | None = None
    ):
        return complete(
            name,
            message,
            system_message,
            temperature,
            max_tokens,
            json,
            schema
        )
    
    return _

    