import enum

"""
from Python documentation: https://docs.python.org/3/library/enum.html#autonumber

I'm Just Copy it~ :D
"""


class Enum(enum.Enum):
    def __new__(cls):
        value = len(cls.__members__) + 1
        obj = object.__new__(cls)
        obj._value_ = value
        return obj
