from enum import Enum
from .base import BaseModel
from .service_schedule import ServiceScheduleModel
from .query import QueryModel

class LimitsModel(BaseModel):
    api_ver: str
    names: list[str]

class GenerationIntervalModel(Enum):
    HOURLY = 'Hourly'
    DAILY = 'Daily'

class AuthModel(BaseModel):
    grant_type: str
    client_id: str
    client_secret: str
    username: str
    password: str

class RedisModel(BaseModel):
    host: str
    port: int
    db_number: int
    password: str
    ssl: bool
    expire_days: int

class ArgumentsModel(BaseModel):
    auth: AuthModel
    redis: RedisModel
    api_ver: str
    token_url: str
    auth_env_prefix: str
    cache_enabled: bool
    date_field: str
    generation_interval: GenerationIntervalModel
    time_lag_minutes: int
    queries: list[QueryModel]
    logs_enabled: bool
    limits: LimitsModel

class InstanceModel(BaseModel):
    name: str
    service_schedule: ServiceScheduleModel
    arguments: ArgumentsModel
    labels: dict[str,str]