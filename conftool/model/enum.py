from enum import Enum

class ConfigEnum(Enum):
    def __str__(self):
        return self._value_