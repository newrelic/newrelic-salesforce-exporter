from .base import BaseModel
from .exception import ConfigException

import validators

class TokenUrlModel(BaseModel):
    __inner_val__: str

    def __init__(self, val: str = ""):
        super().__init__()
        self.__inner_val__ = val

    def check(self):
        if validators.url(self.__inner_val__) != True:
            raise ConfigException(f"Wrong URL format in `token_url`")
        super().check()