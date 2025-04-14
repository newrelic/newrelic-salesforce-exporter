from conftool.model.api_name import ApiNameModel
from .base import BaseModel
from .api_ver import ApiVerModel
from .exception import ConfigException
from .env import EnvModel

class QueryModel(BaseModel):
    query: str
    timestamp_attr: str
    rename_timestamp: str
    api_ver: ApiVerModel
    env: EnvModel
    api_name: ApiNameModel
    event_type: str
    id: list[str]

    def check(self):
        if self.query is None:
            raise ConfigException(f"`query` must be defined")
        return super().check()