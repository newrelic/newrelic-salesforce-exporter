from .base import BaseModel
from .service_schedule import ServiceScheduleModel

class ConfigModel(BaseModel):
    integration_name: str
    run_as_service: bool
    cron_interval_minutes: int
    service_schedule: ServiceScheduleModel