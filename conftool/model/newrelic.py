from .base import BaseModel
from .exception import ConfigException
from .data_format import DataFormatModel
from .api_endpoint import ApiEndpointModel
   
class NewrelicModel(BaseModel):
    data_format: DataFormatModel
    api_endpoint: ApiEndpointModel
    account_id: str
    license_key: str

    def check(self):
        if self.api_endpoint is None:
           raise ConfigException("`api_endpoint` must be defined")
        super().check()