from .base import BaseModel
from .api_ver import ApiVer
from .exception import ConfigException

class Env(BaseModel):
    end_date: str
    start_date: str

    def check(self):
        # No checks required
        return super().check()

class QueryModel(BaseModel):
    query: str
    timestamp_attr: str
    rename_timestamp: str
    api_ver: ApiVer
    env: Env
    api_name: str
    event_type: str
    id: list[str]

    def check(self):
        if self.query is None:
            raise ConfigException(f"`query` must be defined")
        return super().check()