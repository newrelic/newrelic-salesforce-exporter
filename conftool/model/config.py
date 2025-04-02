from .base import BaseModel
from .service_schedule import ServiceScheduleModel
from .instance import InstanceModel
from .query import QueryModel
from .newrelic import NewRelicModel
from .exception import ConfigException

class ConfigModel(BaseModel):
    integration_name: str
    run_as_service: bool
    cron_interval_minutes: int
    service_schedule: ServiceScheduleModel
    instances: list[InstanceModel]
    queries: list[QueryModel]
    newrelic: NewRelicModel

    def check(self):
        if self.run_as_service:
            if self.cron_interval_minutes is not None:
                if self.cron_interval_minutes <= 0:
                    raise ConfigException("`cron_interval_minutes` must be greater than 0")
        else:
            if self.service_schedule is None:
                raise ConfigException("`service_schedule` must be defined")
        if self.instances is None:
            raise ConfigException("`instances` must be defined")
        if len(self.instances) == 0:
            raise ConfigException("`instances` must contain at least one entry")
        if self.newrelic is None:
            raise ConfigException("`newrelic` must be defined")
        super().check()