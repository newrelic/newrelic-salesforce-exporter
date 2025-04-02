from .base import BaseModel
from .service_schedule import ServiceScheduleModel
from .instance import InstanceModel
from .query import QueryModel
from .exception import ConfigException

class ConfigModel(BaseModel):
    integration_name: str
    run_as_service: bool
    cron_interval_minutes: int
    service_schedule: ServiceScheduleModel
    instances: list[InstanceModel]
    queries: list[QueryModel]

    def check(self):
        if self.integration_name is None:
            raise ConfigException("integration_name must be defined")
        if self.integration_name == "":
            raise ConfigException("integration_name can't be empty")
        if self.run_as_service:
            if self.cron_interval_minutes is None:
                raise ConfigException("cron_interval_minutes must be defined")
            if self.cron_interval_minutes <= 0:
                raise ConfigException("cron_interval_minutes must be greater than 0")
        else:
            if self.service_schedule is None:
                raise ConfigException("service_schedule must be set")
        if self.instances is None:
            raise ConfigException("instances must be defined")
        if len(self.instances) == 0:
            raise ConfigException("instances must contain at least one entry")
        super().check()