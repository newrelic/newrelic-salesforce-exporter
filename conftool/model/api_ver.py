from .base import BaseModel
from .exception import ConfigException

class ApiVerModel(BaseModel):
    __inner_val__: str

    def check(self):
        components: list[str] = self.__inner_val__.split(".")
        if len(components) != 2:
            raise ConfigException(f"Wrong api_ver value `{self.__inner_val__}`, it must have the format 'X.Y'")
        for n in components:
            if not n.isnumeric():
                raise ConfigException(f"Wrong api_ver value `{self.__inner_val__}`, components must be numbers")
        super().check()
        