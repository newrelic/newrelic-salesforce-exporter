from .base import BaseModel
from .service_schedule import ServiceScheduleModel
from .instance import InstanceModel
from .query import QueryModel
from .newrelic import NewrelicModel
from .exception import ConfigException
from . import to_dict

import yaml

class ConfigModel(BaseModel):
    integration_name: str
    run_as_service: bool
    cron_interval_minutes: int
    service_schedule: ServiceScheduleModel
    instances: list[InstanceModel]
    queries: list[QueryModel]
    newrelic: NewrelicModel

    def check(self):
        if self.run_as_service:
            if self.cron_interval_minutes is not None:
                if self.cron_interval_minutes <= 0:
                    raise ConfigException("`cron_interval_minutes` must be greater than 0")
        if self.instances is None:
            raise ConfigException("`instances` must be defined")
        if len(self.instances) == 0:
            raise ConfigException("`instances` must contain at least one entry")
        if self.newrelic is None:
            raise ConfigException("`newrelic` must be defined")
        super().check()
    
    def to_yaml(self) -> str:
        return yaml.dump(to_dict(self), sort_keys=False)