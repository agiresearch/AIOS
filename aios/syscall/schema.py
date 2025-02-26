from aios.core.types import DataType

class FieldSchema:
    def __init__(self, key_name: str, data_type: DataType, description: str):
        self.key_name = key_name
        self.data_type = data_type
        self.description = description

    def to_llm_format(self) -> str:
        return f'"{self.key_name}": {self.description} (type is {self.data_type})'

class CoreSchema:
    def __init__(self):
        self.fields: list[FieldSchema] = []

    def add_field(self, key_name: str, data_type: DataType, description: str):
        field = FieldSchema(key_name, data_type, description)
        self.fields.append(field)

        return self

    def to_llm_format(self) -> str:
        formatted_fields = [field.to_llm_format() for field in self.fields]
        return "{\n  " + ",\n  ".join(formatted_fields) + "\n}"
