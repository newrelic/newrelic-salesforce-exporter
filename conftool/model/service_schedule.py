from .base import BaseModel
from .exception import ConfigException

class ServiceScheduleModel(BaseModel):
    hour: str
    minute: str

    def check(self):
        if self.hour is None:
            raise ConfigException(f"service_schedule `hour` can't be none")
        if self.minute is None:
            raise ConfigException(f"service_schedule `minute` can't be none")
        self.check_cron_format('hour', 0, 23, self.hour)
        self.check_cron_format('minute', 0, 59, self.minute)
        super().check()

    def check_cron_format(self, attr_name: str, min: int, max: int, cron_conf: str):
        if cron_conf == '*':
            return
        elif cron_conf == "":
            raise ConfigException(f"service_schedule `{attr_name}` can't be empty")
        else:
            str_nums = cron_conf.split(",")
            last_num = -1
            for n in str_nums:
                try:
                    num = int(n)
                except Exception:
                    raise ConfigException(f"values in service_schedule `{attr_name}` must be valid numbers")
                if num > last_num:
                    last_num = num
                else:
                    raise ConfigException(f"numbers in service_schedule `{attr_name}` must be in ascending order")
                if num < min or num > max:
                    raise ConfigException(f"numbers in service_schedule `{attr_name}` must be in range [{min},{max}]")