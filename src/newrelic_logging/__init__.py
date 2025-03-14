from enum import Enum


# Integration definitions

VERSION         = "2.6.0"
NAME            = "salesforce-exporter"
PROVIDER        = "newrelic-labs"
COLLECTOR_NAME  = "newrelic-salesforce-exporter"


class DataFormat(Enum):
    LOGS = 1
    EVENTS = 2


class ConfigException(Exception):
    def __init__(self, prop_name: str = None, *args: object):
        self.prop_name = prop_name
        super().__init__(*args)


class LoginException(Exception):
    pass


class SalesforceApiException(Exception):
    def __init__(self, err_code: int = 0, *args: object):
        self.err_code = err_code
        super().__init__(*args)


class CacheException(Exception):
    pass


class NewRelicApiException(Exception):
    pass
