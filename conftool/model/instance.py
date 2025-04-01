from enum import Enum
from .base import BaseModel
from .service_schedule import ServiceScheduleModel
from .query import QueryModel
from .api_ver import ApiVer

import validators

class LimitsModel(BaseModel):
    api_ver: ApiVer
    names: list[str]

class GenerationIntervalModel(Enum):
    HOURLY = 'Hourly'
    DAILY = 'Daily'

#TODO: add attributes for the JWT flow
class AuthModel(BaseModel):
    grant_type: str
    client_id: str
    client_secret: str
    username: str
    password: str

    def check(self):
        #TODO: check
        pass

class RedisModel(BaseModel):
    host: str
    port: int
    db_number: int
    password: str
    ssl: bool
    expire_days: int

    def check(self):
        if validators.domain(self.host) != True and \
           validators.ipv4(self.host) != True and \
           validators.ipv6(self.host) != True:
            raise Exception(f"`host` must be a valid domain name or IP address")
        if self.port < 0 or self.port > 65535:
            raise Exception(f"`port` is `{self.port}` and must be a valid TCP port value [0, 65535]")
        if self.db_number < 0 or self.db_number > 15:
            raise Exception(f"`db_number` must be a valid Redis DB number [0, 15]")
        if self.expire_days < 0:
            raise Exception(f"`expire_days` can't be negative")

class ArgumentsModel(BaseModel):
    auth: AuthModel
    redis: RedisModel
    api_ver: ApiVer
    token_url: str
    auth_env_prefix: str
    cache_enabled: bool
    date_field: str
    generation_interval: GenerationIntervalModel
    time_lag_minutes: int
    queries: list[QueryModel]
    logs_enabled: bool
    limits: LimitsModel

    def check(self):
        if validators.url(self.token_url) != True:
            raise Exception(f"Wrong URL format in `token_url`")
        if self.time_lag_minutes < 0:
            raise Exception(f"`time_lag_minutes`, can't be negative")

class InstanceModel(BaseModel):
    name: str
    service_schedule: ServiceScheduleModel
    arguments: ArgumentsModel
    labels: dict[str,str]