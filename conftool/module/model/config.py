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