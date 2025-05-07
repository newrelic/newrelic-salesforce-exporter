from .base import BaseModel
from .service_schedule import ServiceScheduleModel
from .exception import ConfigException
from .arguments import ArgumentsModel

class InstanceModel(BaseModel):
    name: str
    service_schedule: ServiceScheduleModel
    arguments: ArgumentsModel
    labels: dict[str,str]

    def check(self):
        if self.name is None or self.name == "":
            raise ConfigException(f"`name` must be defined")
        if self.arguments is None:
            raise ConfigException(f"`arguments` must be defined")
        super().check()