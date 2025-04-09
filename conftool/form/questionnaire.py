from conftool.model.config import ConfigModel
from conftool.model.exception import ConfigException
from conftool.model.instance import InstanceModel
from conftool.model.service_schedule import ServiceScheduleModel
from .question import Question, ask_int, ask_enum, ask_bool, ask_str, ask_any
from .text import *

def run():
    conf = ConfigModel()

    # Integration name
    conf.integration_name = \
    ask_any(Question(
        text=t_integration_name,
        required=False))

    # Run as service
    conf.run_as_service = \
    ask_bool(Question(
        text=t_run_as_service,
        required=False))

    if conf.run_as_service is None or conf.run_as_service == False:
        conf.cron_interval_minutes = \
        ask_int(Question(
            text=t_cron_interval,
            required=False),
            1, 10000)
    else:
        do_setup_service_schedule = \
        ask_bool(Question(
            text=t_conf_scheduler,
            required=True))

        if do_setup_service_schedule:
            service_schedule = ServiceScheduleModel()
            service_schedule.hour = \
            ask_str(Question(
                text=t_service_scheduler_hours,
                required=True),
                cron_config_check_hours)
            service_schedule.minute = \
            ask_str(Question(
                text=t_service_scheduler_mins,
                required=True),
                cron_config_check_minutes)
            conf.service_schedule = service_schedule

    # Instances
    conf.instances = list()
    num_instances = \
    ask_int(Question(
        text=t_num_instances,
        required=True),
        1, 10)

    for _ in range(num_instances):
        i = instance_questions()
        conf.instances.append(i)

    print("Final config model:\n")
    print(conf.to_yaml())

    # ask_enum(Question(
    #     text="New Relic API endpoint",
    #     required=False,
    #     prompt="API Endpoint (1-3)?",
    #     datatype=ApiEndpointModel))

def instance_questions() -> InstanceModel:
    pass

# Format checkers

def cron_config_check_hours(text: str) -> bool:
    try:
        ServiceScheduleModel().check_cron_format('hour', 0, 23, text)
    except ConfigException:
        return False
    return True

def cron_config_check_minutes(text: str) -> bool:
    try:
        ServiceScheduleModel().check_cron_format('minute', 0, 59, text)
    except ConfigException:
        return False
    return True