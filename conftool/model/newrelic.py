from .base import BaseModel
from .enum import ConfigEnum
from .exception import ConfigException

class DataFormatModel(ConfigEnum):
   EVENTS = "events"
   LOGS = "logs"

class ApiEndpointModel(ConfigEnum):
   US = "US"
   EU = "EU"
   FEDRAMP = "FEDRAMP"
   
class NewrelicModel(BaseModel):
    data_format: DataFormatModel
    api_endpoint: ApiEndpointModel
    account_id: str
    license_key: str

    def check(self):
        if self.api_endpoint is None:
           raise ConfigException("`api_endpoint` must be defined")
        if self.data_format is DataFormatModel.EVENTS and \
           self.account_id is None:
           raise ConfigException("`account_id` must be defined")
        if self.license_key is None:
            raise ConfigException("`license_ley` must be defined")
        return super().check()