from .base import BaseModel
from .exception import ConfigException

import validators

class RedisModel(BaseModel):
    host: str
    port: int
    db_number: int
    password: str
    ssl: bool
    expire_days: int

    def check(self):
        if self.password is None:
            raise ConfigException(f"`password` is required")
        if self.host is not None:
            if validators.domain(self.host) != True and \
               validators.ipv4(self.host) != True and \
               validators.ipv6(self.host) != True:
                raise ConfigException(f"`host` must be a valid domain name or IP address")
        if self.port is not None:
            if self.port < 0 or self.port > 65535:
                raise ConfigException(f"`port` is `{self.port}` and must be a valid TCP port value [0, 65535]")
        if self.db_number is not None:
            if self.db_number < 0 or self.db_number > 15:
                raise ConfigException(f"`db_number` must be a valid Redis DB number [0, 15]")
        if self.expire_days is not None:
            if self.expire_days < 0:
                raise ConfigException(f"`expire_days` can't be negative")
        super().check()