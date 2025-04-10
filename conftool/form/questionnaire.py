from conftool.model.api_ver import ApiVerModel
from conftool.model.arguments import ArgumentsModel
from conftool.model.auth import AuthModel
from conftool.model.config import ConfigModel
from conftool.model.exception import ConfigException
from conftool.model.grant_type import GrantTypeModel
from conftool.model.instance import InstanceModel
from conftool.model.service_schedule import ServiceScheduleModel
from .question import Question, ask_int, ask_enum, ask_bool, ask_str, ask_any
from .text import *

import validators

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
        service_schedule = ServiceScheduleModel()
        service_schedule.hour = \
        ask_str(Question(
            text=t_service_scheduler_hours,
            required=False),
            cron_hours_check)
        if service_schedule.hour is not None:
            service_schedule.minute = \
            ask_str(Question(
                text=t_service_scheduler_mins,
                required=True),
                cron_minutes_check)
            conf.service_schedule = service_schedule

    # Instances
    conf.instances = list()
    num_instances = \
    ask_int(Question(
        text=t_num_instances,
        required=True),
        1, 10)

    for index in range(num_instances):
        i = instance_questions(index)
        conf.instances.append(i)
    
    #TODO: queries
    #TODO: newrelic

    print("Final config model:\n")
    print(conf.to_yaml())

def instance_questions(index: int) -> InstanceModel:
    print(f"Configuration for Instance #{index+1}\n")
    i = InstanceModel()
    i.name = \
    ask_any(Question(
        text=t_instance_name,
        required=True))
    i.arguments = arguments_questions()
    #TODO: instance-specific service_schedule (only if run_as_service is True). Optional.
    #TODO: labels. Optional.

    return i

def arguments_questions() -> ArgumentsModel:
    args = ArgumentsModel()
    args.token_url = \
    ask_str(Question(
        text=t_token_url,
        required=True),
        token_url_check)
    args.api_ver = \
    ask_str(Question(
        text=t_api_ver,
        required=False),
        api_ver_check)
    do_config_auth = \
    ask_bool(Question(
        text=t_conf_auth,
        required=True))
    if do_config_auth:
        args.auth = auth_questions()
    #TODO: cache/redis config
    #TODO: auth_env_prefix
    #TODO: date_field
    #TODO: generation_interval
    #TODO: time_lag_minutes
    #TODO: queries
    #TODO: limits
    #TODO: logs_enabled
    return args

def auth_questions() -> AuthModel:
    auth = AuthModel()
    auth.grant_type = \
    ask_enum(Question(
        text=t_grant_type,
        required=True,
        datatype=GrantTypeModel))
    auth.client_id = \
    ask_any(Question(
        text=t_client_id,
        required=True))
    if auth.grant_type == GrantTypeModel.PASSWORD:
        auth.client_secret = \
        ask_any(Question(
            text=t_client_secret,
            required=True))
        auth.username = \
        ask_any(Question(
            text=t_username,
            required=True))
        auth.password = \
        ask_any(Question(
            text=t_password,
            required=True))
    else:
        auth.private_key = \
        ask_any(Question(
            text=t_private_key,
            required=True))
        auth.subject = \
        ask_any(Question(
            text=t_subject,
            required=True))
        auth.audience = \
        ask_any(Question(
            text=t_audience,
            required=True))
        auth.expiration_offset = \
        ask_int(Question(
            text=t_expiration_offset,
            required=True),
            0, 100)
    return auth

# Format checkers

def cron_hours_check(text: str) -> bool:
    try:
        ServiceScheduleModel().check_cron_format('hour', 0, 23, text)
    except ConfigException:
        return False
    return True

def cron_minutes_check(text: str) -> bool:
    try:
        ServiceScheduleModel().check_cron_format('minute', 0, 59, text)
    except ConfigException:
        return False
    return True

def token_url_check(text: str) -> bool:
    if validators.url(text) == True:
        return True
    else:
        return False
    
def api_ver_check(text: str) -> bool:
    try:
        ApiVerModel(text).check()
        return True
    except ConfigException:
        return False