from pydantic import BaseModel, ValidationError
from typing import Callable, Type

def validate(model_class: Type[BaseModel]):
    """
    Decorator factory to validate and parse parameters using a specified Pydantic model.

    :param model_class: The Pydantic model class to validate against
    """
    def decorator(func: Callable):
        def wrapper(*args, **kwargs):
            try:
                params = model_class(**kwargs)

                return func(params)
            except ValidationError as e:
                print(f"Validation error: {e}")
                return None
        return wrapper
    return decorator
