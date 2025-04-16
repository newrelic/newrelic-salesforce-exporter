from conftool.model.api_endpoint import ApiEndpointModel
from conftool.model.api_name import ApiNameModel
from conftool.model.api_ver import ApiVerModel
from conftool.model.arguments import ArgumentsModel
from conftool.model.auth import AuthModel
from conftool.model.config import ConfigModel
from conftool.model.data_format import DataFormatModel
from conftool.model.exception import ConfigException
from conftool.model.generation_interval import GenerationIntervalModel
from conftool.model.grant_type import GrantTypeModel
from conftool.model.instance import InstanceModel
from conftool.model.limits import LimitsModel
from conftool.model.newrelic import NewrelicModel
from conftool.model.query import QueryModel
from conftool.model.redis import RedisModel
from conftool.model.service_schedule import ServiceScheduleModel
from .question import Question, ask_int, ask_enum, ask_bool, ask_str, ask_any, \
                                ask_dict, print_title, print_warning, \
                                push_level, pop_level
from .text import *

import validators

def run() -> ConfigModel:
    push_level("Config")
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

    if conf.run_as_service == True:
        conf.service_schedule = service_schedule_questions()
    else:
        conf.cron_interval_minutes = \
        ask_int(Question(
            text=t_cron_interval,
            required=False),
            1, 10000)

    # Instances
    conf.instances = list()
    num_instances = \
    ask_int(Question(
        text=t_num_instances,
        required=True),
        1, 10)

    for index in range(num_instances):
        print_title(f"Configuration for Instance #{index+1}")
        i = instance_questions(conf.run_as_service, index + 1)
        conf.instances.append(i)
    
    # Queries
    conf.queries = queries_questions(requird=True, text=t_num_queries)

    # Newrelic
    conf.newrelic = newrelic_questions()

    pop_level()

    return conf

def instance_questions(run_as_service: bool, num: int) -> InstanceModel:
    push_level(f"Instance #{num}")
    i = InstanceModel()
    i.name = \
    ask_any(Question(
        text=t_instance_name,
        required=True))
    i.arguments = arguments_questions()
    i.labels = \
    ask_dict(Question(
        text=t_instance_labels,
        required=False),
        id_check, id_check)
    if run_as_service == True:
        i.service_schedule = service_schedule_questions()

    pop_level()
    return i

def service_schedule_questions() -> ServiceScheduleModel:
    push_level("Service schedule")
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
        pop_level()
        return service_schedule
    else:
        pop_level()
        return None

def arguments_questions() -> ArgumentsModel:
    push_level("Arguments")
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
    else:
        print_warning("Auth data is REQUIRED.\nIf you don't set it in the config file, you MUST provide it as env variables. Check the documentation for details.")
    args.cache_enabled = \
    ask_bool(Question(
        text=t_cache_enabled,
        required=False))
    if args.cache_enabled == True:
        args.redis = redis_questions()
    args.auth_env_prefix = \
    ask_any(Question(
        text=t_auth_env_prefix,
        required=False))
    args.date_field = \
    ask_any(Question(
        text=t_date_field,
        required=False))
    args.generation_interval = \
    ask_enum(Question(
        text=t_generation_interval,
        required=False,
        datatype=GenerationIntervalModel))
    args.time_lag_minutes = \
    ask_int(Question(
        text=t_time_lag_minutes,
        required=False),
        0, 1000)
    args.logs_enabled = \
    ask_bool(Question(
        text=t_logs_enabled,
        required=False))
    args.queries = queries_questions(requird=False, text=t_num_queries_instance)
    args.limits = limits_questions()
    pop_level()
    return args

def limits_questions() -> LimitsModel:
    push_level("Limits")
    do_limits = \
    ask_bool(Question(
        text=t_conf_limits,
        required=True))
    if do_limits:
        limits = LimitsModel()
        api_ver = \
        ask_str(Question(
            text=t_api_ver,
            required=False),
            api_ver_check)
        limits.api_ver = ApiVerModel(api_ver)
        limits.event_type = \
        ask_str(Question(
            text=t_limits_event_type,
            required=False),
            id_check)
        name_list = \
        ask_str(Question(
            text=t_limits_name_list,
            required=False),
            id_list_check)
        if name_list is None:
            limits.names = None
        else:
            # split and clean comma separated values
            limits.names = [x.strip() for x in name_list.split(",")]
        pop_level()
        return limits
    else:
        pop_level()
        return None

def auth_questions() -> AuthModel:
    push_level("Auth")
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
    pop_level()
    return auth

def redis_questions() -> RedisModel:
    push_level("Redis")
    redis = RedisModel()
    redis.host = \
    ask_str(Question(
        text=t_redis_host,
        required=False),
        host_check)
    redis.port = \
    ask_int(Question(
        text=t_redis_post,
        required=False),
        0, 65535)
    redis.db_number = \
    ask_int(Question(
        text=t_redis_dbnum,
        required=False),
        0, 16)
    redis.ssl = \
    ask_bool(Question(
        text=t_redis_ssl,
        required=False))
    redis.password = \
    ask_any(Question(
        text=t_redis_password,
        required=False))
    if redis.password is None:
        redis.password = ""
    redis.expire_days = \
    ask_int(Question(
        text=t_redis_expire,
        required=False),
        0, 100)
    pop_level()
    return redis

def query_questions(num: int) -> QueryModel:
    push_level(f"Query #{num}")
    query = QueryModel()
    query.query = \
    ask_any(Question(
        text=t_query_query,
        required=True))
    api_ver = \
    ask_str(Question(
        text=t_api_ver,
        required=False),
        api_ver_check)
    query.api_ver = ApiVerModel(api_ver)
    query.api_name = \
    ask_enum(Question(
        text=t_query_api_name,
        required=False,
        datatype=ApiNameModel))
    query.event_type = \
    ask_any(Question(
        text=t_query_event_type,
        required=False))
    query.timestamp_attr = \
    ask_any(Question(
        text=t_query_timestamp_attr,
        required=False))
    query.rename_timestamp = \
    ask_any(Question(
        text=t_query_rename_timestamp,
        required=False))
    id_list = \
    ask_str(Question(
        text=t_query_id_list,
        required=False),
        id_list_check)
    if id_list is None:
        query.id = None
    else:
        # split and clean comma separated values
        query.id = [x.strip() for x in id_list.split(",")]
    query.env = \
    ask_dict(Question(
        text=t_query_env,
        required=False),
        id_check, lambda _: True)
    pop_level()
    return query

def queries_questions(requird: bool, text: Text) -> list[QueryModel]:
    push_level("Queries")
    queries = list()
    if requird:
        min_queries = 1
    else:
        min_queries = 0
    num_queries = \
    ask_int(Question(
        text=text,
        required=True),
        min_queries, 10)
    for index in range(num_queries):
        print_title(f"Configuration for query #{index+1}")
        q = query_questions(index+1)
        queries.append(q)
    if len(queries) == 0:
        pop_level()
        return None
    else:
        pop_level()
        return queries

def newrelic_questions() -> NewrelicModel:
    push_level("Newrelic")
    newrelic = NewrelicModel()
    newrelic.data_format = \
    ask_enum(Question(
        text=t_nr_data_format,
        required=False,
        datatype=DataFormatModel))
    newrelic.api_endpoint = \
    ask_enum(Question(
        text=t_nr_api_endpoint,
        required=True,
        datatype=ApiEndpointModel))
    if newrelic.data_format == DataFormatModel.EVENTS:
        newrelic.account_id = \
        ask_str(Question(
            text=t_nr_account_id,
            required=True),
            numeric_check)
    newrelic.license_key = \
    ask_any(Question(
        text=t_nr_license_key,
        required=True))
    pop_level()
    return newrelic

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
    
def host_check(text: str) -> bool:
    if validators.domain(text) != True and \
       validators.ipv4(text) != True and \
       validators.ipv6(text) != True:
        return False
    else:
        return True
    
def numeric_check(text: str) -> bool:
    return text.isnumeric()

def id_list_check(text: str) -> bool:
    elements = text.split(",")
    valids_elements = [x.strip() for x in elements if x.strip().isidentifier()]
    return len(valids_elements) == len(elements)

def id_check(text: str) -> bool:
    return text.isidentifier()