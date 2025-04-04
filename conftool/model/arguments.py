from .base import BaseModel
from .generation_interval import GenerationIntervalModel
from .auth import AuthModel
from .redis import RedisModel
from .api_ver import ApiVerModel
from .date_field import DateFieldModel
from .query import QueryModel
from .limits import LimitsModel
from .exception import ConfigException

import validators

class ArgumentsModel(BaseModel):
    auth: AuthModel
    redis: RedisModel
    api_ver: ApiVerModel
    token_url: str
    auth_env_prefix: str
    cache_enabled: bool
    date_field: DateFieldModel
    generation_interval: GenerationIntervalModel
    time_lag_minutes: int
    queries: list[QueryModel]
    logs_enabled: bool
    limits: LimitsModel

    def check(self):
        if self.token_url is None:
            raise ConfigException(f"`token_url` is required")
        if validators.url(self.token_url) != True:
            raise ConfigException(f"Wrong URL format in `token_url`")
        if self.cache_enabled:
            if self.redis is None:
                raise ConfigException(f"`redis` must be defined when `cache_enabled` is True")
        if self.time_lag_minutes is not None:
            if self.time_lag_minutes < 0:
                raise ConfigException(f"`time_lag_minutes` can't be negative")
        super().check()