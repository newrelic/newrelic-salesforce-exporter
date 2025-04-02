from .base import BaseModel
from .service_schedule import ServiceScheduleModel
from .query import QueryModel
from .api_ver import ApiVer
from .exception import ConfigException
from .config_enum import ConfigEnum

import validators

class LimitsModel(BaseModel):
    api_ver: ApiVer
    names: list[str]

    def check(self):
        #TODO: check
        super().check()

class GenerationIntervalModel(ConfigEnum):
    HOURLY = 'Hourly'
    DAILY = 'Daily'

class GrantTypeModel(ConfigEnum):
    PASSWORD = "password"
    JWT = "urn:ietf:params:oauth:grant-type:jwt-bearer"

class AuthModel(BaseModel):
    grant_type: GrantTypeModel
    client_id: str
    # Password flow only attributes
    client_secret: str
    username: str
    password: str
    # JWT flow only attributes
    private_key: str
    subject: str
    audience: str
    expiration_offset: int

    def check(self):
        if self.grant_type is None:
            raise ConfigException(f"`grant_type` must be defined")
        if self.client_id is None:
            raise ConfigException(f"`client_id` must be defined")
        if self.grant_type == GrantTypeModel.PASSWORD:
            self._pass_flow_check()
        else:
            self._jwt_flow_check()
        super().check()

    def _pass_flow_check(self):
        if self.client_secret is None:
            raise ConfigException(f"`client_secret` must be defined")
        if self.username is None:
            raise ConfigException(f"`username` must be defined")
        if self.password is None:
            raise ConfigException(f"`password` must be defined")

    def _jwt_flow_check(self):
        if self.private_key is None:
            raise ConfigException(f"`private_key` must be defined")
        if self.subject is None:
            raise ConfigException(f"`subject` must be defined")
        if self.audience is None:
            raise ConfigException(f"`audience` must be defined")
        if self.expiration_offset is not None:
            if self.expiration_offset < 0:
                raise ConfigException(f"`expiration_offset` can't be negative")

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

class DateFieldModel(ConfigEnum):
    LOGDATE = "LogDate"
    CREATEDDATE = "CreatedDate"

class ArgumentsModel(BaseModel):
    auth: AuthModel
    redis: RedisModel
    api_ver: ApiVer
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

class InstanceModel(BaseModel):
    name: str
    service_schedule: ServiceScheduleModel
    arguments: ArgumentsModel
    labels: dict[str,str]

    def check(self):
        if self.name is None or self.name == "":
            raise ConfigException(f"`name` must be defined")
        if self.arguments is None:
            raise ConfigException(f"`arguments` must be defined")
        return super().check()