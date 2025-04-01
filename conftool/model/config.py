from .base import BaseModel
from .service_schedule import ServiceScheduleModel
from .instance import InstanceModel
from .query import QueryModel

class ConfigModel(BaseModel):
    integration_name: str
    run_as_service: bool
    cron_interval_minutes: int
    service_schedule: ServiceScheduleModel
    instances: list[InstanceModel]
    queries: list[QueryModel]

    def check(self):
        if self.integration_name == "":
            raise Exception("integration_name can't be empty")
        if self.cron_interval_minutes <= 0:
            raise Exception("cron_interval_minutes must be greater than 0")
        if len(self.instances) == 0:
            raise Exception("instances must contain at least one entry")