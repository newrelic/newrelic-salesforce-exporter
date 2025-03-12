#!/usr/bin/env python
import newrelic.agent
newrelic.agent.initialize('./newrelic.ini')


import optparse
import os
from pytz import utc
import sys
from typing import Any
from yaml import Loader, load


from apscheduler.executors.pool import ThreadPoolExecutor
from apscheduler.jobstores.memory import MemoryJobStore
from apscheduler.schedulers.background import BlockingScheduler


from newrelic_logging.config import Config, getenv
from newrelic_logging.factory import Factory
from newrelic_logging.limits import receiver as limits_receiver
from newrelic_logging.query import QueryFactory, receiver as query_receiver
from newrelic_logging.telemetry import print_info, print_warn


CONFIG_DIR = 'CONFIG_DIR'
DEFAULT_CONFIG_FILE = 'config.yml'
DEFAULT_EVENT_TYPE_FIELDS_MAPPING_FILE = 'event_type_fields.yml'
DEFAULT_NUMERIC_FIELDS_MAPPING_FILE = 'numeric_fields.yml'
QUERIES = 'queries'
MAPPING = 'mapping'
SERVICE_SCHEDULE = 'service_schedule'
CRON_INTERVAL_MINUTES = 'cron_interval_minutes'
RUN_AS_SERVICE = 'run_as_service'
DEFAULT_NUMERIC_FIELDS_MAPPING = {
    "Common":
    [
        'EXEC_TIME', 'RUN_TIME', 'NUMBER_OF_INTERVIEWS',
        'NUMBER_COLUMNS', 'NUM_SESSIONS', 'CPU_TIME', 'EPT',
        'DB_CPU_TIME', 'VIEW_STATE_SIZE', 'ROWS_PROCESSED',
        'RESPONSE_SIZE', 'PAGE_START_TIME', 'NUMBER_EXCEPTION_FILTERS',
        'BROWSER_DEVICE_TYPE', 'NUMBER_FIELDS', 'CALLOUT_TIME',
        'DURATION', 'STATUS_CODE', 'DB_BLOCKS', 'NUMBER_OF_RECORDS',
        'TOTAL_TIME', 'RECORDS_FAILED','ROW_COUNT', 'AVERAGE_ROW_SIZE',
        'DB_TOTAL_TIME', 'READ_TIME', 'REQUEST_SIZE',
        'EFFECTIVE_PAGE_TIME', 'RESULT_SIZE_MB', 'RECORDS_PROCESSED',
        'NUM_CLICKS', 'NUMBER_BUCKETS', 'TOTAL_EXECUTION_TIME',
        'NUMBER_SOQL_QUERIES', 'FLOW_LOAD_TIME', 'REOPEN_COUNT',
        'NUMBER_OF_ERRORS', 'LIMIT_USAGE_PERCENT',
    ]
}


def parse_args() -> optparse.Values:
    # Create the parser object
    parser = optparse.OptionParser()

    # Populate options
    parser.add_option(
        '-c',
        '--config_dir',
        default=None,
        help='directory containing configuration files',
    )

    parser.add_option(
        '-f',
        '--config_file',
        default=DEFAULT_CONFIG_FILE,
        help='name of configuration file',
    )

    parser.add_option(
        '-e',
        '--event_type_fields_mapping',
        default=DEFAULT_EVENT_TYPE_FIELDS_MAPPING_FILE,
        help='name of event type fields mapping file',
    )

    parser.add_option(
        '-n',
        '--num_fields_mapping',
        default=DEFAULT_NUMERIC_FIELDS_MAPPING_FILE,
        help='name of numeric fields mapping file',
    )

    # Parse arguments
    (values, _) = parser.parse_args()

    return values


def load_config(config_path: str) -> Config:
    if not os.path.exists(config_path):
        sys.exit(f'config file {config_path} not found')

    with open(config_path) as stream:
        config = load(stream, Loader=Loader)

    new_queries = []
    if QUERIES in config:
        for query in config[QUERIES]:
            if type(query) is str:
                with open(query) as stream:
                    sub_query_config = load(stream, Loader=Loader)
                if QUERIES in sub_query_config \
                    and type(sub_query_config[QUERIES]) is list:
                    new_queries = new_queries + sub_query_config[QUERIES]
                else:
                    print_warn("Malformed subconfig file. Ignoring")
            elif type(query) is dict:
                new_queries.append(query)
            else:
                print_warn("Malformed 'queries' member in config, expected either dictionaries or strings in the array. Ignoring.")
                pass
    config[QUERIES] = new_queries

    return Config(config)


def load_mapping_file(mapping_file_path: str, default_mapping: Any) -> dict:
    if not os.path.exists(mapping_file_path):
        print_info(f'mapping file {mapping_file_path} not found, using default mapping')
        return default_mapping

    with open(mapping_file_path) as stream:
        return load(stream, Loader=Loader)[MAPPING]


def create_receivers(
    config: Config,
    event_type_fields_mapping: dict,
    initial_delay: int,
):
    receivers = []

    receivers.append(
        query_receiver.new_create_receiver_func(
            config,
            QueryFactory(),
            event_type_fields_mapping,
            initial_delay,
        )
    )

    receivers.append(
        limits_receiver.new_create_receiver_func()
    )

    return receivers


def run_once(
    factory: Factory,
    config: Config,
    receivers: list[callable],
    numeric_fields_list: set
):
    # Run the integration
    factory.new_integration(
        factory,
        config,
        receivers,
        numeric_fields_list,
    ).run()


def run_as_service(
    factory: Factory,
    config: Config,
    receivers: list[callable],
    numeric_fields_list: set,
):
    scheduler = BlockingScheduler(
        jobstores={ 'default': MemoryJobStore() },
        # NOTE: I have serious doubts regarding the thread-safety of `Integration.run()`,
        #       so until provent to be safe, we better use a single thread for the scheduler.
        #       This way jobs are executed one after the other.
        executors={ 'default': ThreadPoolExecutor(1) },
        job_defaults={
            'coalesce': False,
            'max_instances': 5
        },
        timezone=utc
    )

    if SERVICE_SCHEDULE in config:
        service_schedule = config[SERVICE_SCHEDULE]
    else:
        # use instance-specific SERVICE_SCHEDULE config
        service_schedule = None

    # build one scheduler job per instance
    for index, i in enumerate(config['instances']):
        if service_schedule is None:
            if SERVICE_SCHEDULE not in i:
                raise Exception('"run_as_service" configured but no "service_schedule" property found, either general or instance specific')
            
            sched_conf = i[SERVICE_SCHEDULE]
            sched_hours = sched_conf['hour']
            sched_minutes = sched_conf['minute']
        else:
            sched_hours = service_schedule['hour']
            sched_minutes = service_schedule['minute']

        scheduler.add_job(
            factory.new_integration(
                factory,
                config,
                receivers,
                numeric_fields_list,
                # pass index to know the exact instance we need to create the new integration
                index
            ).run,
            trigger='cron',
            hour=sched_hours,
            minute=sched_minutes,
            second='0',
        )

    print_info('Press Ctrl+{0} to exit'.format('Break' if os.name == 'nt' else 'C'))
    scheduler.start()


def run(
    config: Config,
    event_type_fields_mapping: dict,
    numeric_fields_list: set
):
    factory = Factory()

    if not config.get(RUN_AS_SERVICE, False):
        run_once(
            factory,
            config,
            create_receivers(
                config,
                event_type_fields_mapping,
                config.get_int(CRON_INTERVAL_MINUTES, 60),
            ),
            numeric_fields_list,
        )
        return


    run_as_service(
        factory,
        config,
        create_receivers(
            config,
            event_type_fields_mapping,
            0,
        ),
        numeric_fields_list,
    )


@newrelic.agent.background_task()
def main():
    print_info(f'Integration start. Using program arguments {sys.argv[1:]}')

    # Parse command line arguments
    options = parse_args()

    # Initialize vars from options
    config_dir = options.config_dir
    if config_dir == None:
        config_dir = getenv(CONFIG_DIR, os.getcwd())

    # Load config
    config = load_config(f'{config_dir}/{options.config_file}')

    # Initialize event mappings
    event_type_fields_mapping = load_mapping_file(
        f'{config_dir}/{options.event_type_fields_mapping}',
        {},
    )

    # Initialize numeric field mapping
    numeric_fields_mapping = load_mapping_file(
        f'{config_dir}/{options.num_fields_mapping}',
        DEFAULT_NUMERIC_FIELDS_MAPPING,
    )

    # Build the numeric fields list
    numeric_fields_list = set()
    for event_num_fields in numeric_fields_mapping.values():
        for num_field in event_num_fields:
            numeric_fields_list.add(num_field)

    # Run the application or startup the service
    run(config, event_type_fields_mapping, numeric_fields_list)

    print_info("Integration end.")


if __name__ == "__main__":
    main()
