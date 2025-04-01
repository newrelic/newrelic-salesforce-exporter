from .base import BaseModel
from .api_ver import ApiVer

class Env(BaseModel):
    end_date: str
    start_date: str

class QueryModel(BaseModel):
    query: str
    timestamp_attr: str
    rename_timestamp: str
    api_ver: ApiVer
    env: Env
    api_name: str