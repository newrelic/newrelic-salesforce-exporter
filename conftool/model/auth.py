from .base import BaseModel
from .exception import ConfigException
from .grant_type import GrantTypeModel

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
