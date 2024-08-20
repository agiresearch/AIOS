from typing import Union

class DataType:
    def __init__(self, type_name: str, subtype: Union['DataType', None] = None):
        self.type_name = type_name
        self.subtype = subtype  # For handling complex types like arrays or objects

    def __str__(self) -> str:
        if self.subtype:
            return f"{self.type_name}[{self.subtype}]"
        return self.type_name

# Type instances for primitive types
string = DataType("string")
_float = DataType("float")
integer = DataType("integer")
boolean = DataType("boolean")
null = DataType("null")

# Function for complex types
def _obj(properties: dict = None) -> DataType:
    return DataType("object", properties)

def array(subtype: DataType) -> DataType:
    return DataType("array", subtype)