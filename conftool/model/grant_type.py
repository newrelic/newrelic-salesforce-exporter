from .config_enum import ConfigEnum

class GrantTypeModel(ConfigEnum):
    PASSWORD = "password"
    JWT = "urn:ietf:params:oauth:grant-type:jwt-bearer"
