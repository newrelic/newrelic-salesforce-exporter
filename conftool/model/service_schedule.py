from .base import BaseModel

class ServiceScheduleModel(BaseModel):
    hour: str
    minute: str

    def check(self):
        self.check_cron_format('hour', 0, 23, self.hour)
        self.check_cron_format('minute', 0, 59, self.minute)
        super().check()

    def check_cron_format(self, attr_name: str, min: int, max: int, cron_conf: str):
        if cron_conf == '*':
            return
        elif cron_conf == "":
            raise Exception(f"service_schedule `{attr_name}` can't be empty")
        else:
            str_nums = cron_conf.split(",")
            last_num = -1
            for n in str_nums:
                try:
                    num = int(n)
                except Exception:
                    raise Exception(f"values in service_schedule `{attr_name}` must be valid numbers")
                if num > last_num:
                    last_num = num
                else:
                    raise Exception(f"numbers in service_schedule `{attr_name}` must be in ascending order")
                if num < min or num > max:
                    raise Exception(f"numbers in service_schedule `{attr_name}` must be in range [{min},{max}]")