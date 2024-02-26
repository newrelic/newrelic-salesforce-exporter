#!/usr/bin/env python
import getopt
import os
import sys

from apscheduler.executors.pool import ThreadPoolExecutor
from apscheduler.jobstores.memory import MemoryJobStore
from apscheduler.schedulers.background import BlockingScheduler
from pytz import utc
from yaml import Loader, load
from newrelic_logging.config import getenv
from newrelic_logging.integration import Integration
from newrelic_logging.telemetry import print_info, print_warn

config_dir = None
argv = sys.argv[1:]
print_info(f'Integration start. Using program arguments {argv}')
try:
    opts, args = getopt.getopt(argv, 'c:', ['config_dir='])
    for opt, arg in opts:
        if opt in ('-c', '--config_dir'):
            config_dir = arg

except getopt.GetoptError as e:
    sys.exit(f'error parsing command line options: {e}')

if config_dir is None:
    config_dir = os.environ.get('CONFIG_DIR')
    if config_dir is None:
        config_dir = os.getcwd()

config_file = f'{config_dir}/config.yml'

if not os.path.exists(config_file):
    sys.exit(f'config file {config_file} not found')

event_mapping_file = f'{config_dir}/event_type_fields.yml'
numeric_fields_file = f'{config_dir}/numeric_fields.yml'

def main():
    config = load_config(config_file)

    if not os.path.exists(event_mapping_file):
        print_info(f'event_mapping_file {event_mapping_file} not found, so event mapping will not be used')
        event_mapping = {}
    else:
        with open(event_mapping_file) as stream:
            event_mapping = load(stream, Loader=Loader)['mapping']

    if not os.path.exists(numeric_fields_file):
        print_info(f'numeric_fields_file {numeric_fields_file} not found')
        numeric_fields_mapping = {"Common",
                                  ['EXEC_TIME', 'RUN_TIME', 'NUMBER_OF_INTERVIEWS', 'NUMBER_COLUMNS', 'NUM_SESSIONS',
                                   'CPU_TIME', 'EPT', 'DB_CPU_TIME', 'VIEW_STATE_SIZE', 'ROWS_PROCESSED',
                                   'RESPONSE_SIZE', 'PAGE_START_TIME', 'NUMBER_EXCEPTION_FILTERS',
                                   'BROWSER_DEVICE_TYPE', 'NUMBER_FIELDS', 'CALLOUT_TIME', 'DURATION',
                                   'STATUS_CODE', 'DB_BLOCKS', 'NUMBER_OF_RECORDS', 'TOTAL_TIME', 'RECORDS_FAILED',
                                   'ROW_COUNT', 'AVERAGE_ROW_SIZE', 'DB_TOTAL_TIME',
                                   'READ_TIME', 'REQUEST_SIZE', 'EFFECTIVE_PAGE_TIME', 'RESULT_SIZE_MB',
                                   'RECORDS_PROCESSED', 'NUM_CLICKS', 'NUMBER_BUCKETS', 'TOTAL_EXECUTION_TIME',
                                   'NUMBER_SOQL_QUERIES', 'FLOW_LOAD_TIME', 'REOPEN_COUNT', 'NUMBER_OF_ERRORS',
                                   'LIMIT_USAGE_PERCENT']}
    else:
        with open(numeric_fields_file) as stream:
            numeric_fields_mapping = load(stream, Loader=Loader)['mapping']

    numeric_fields_list = set()
    for event_num_fields in numeric_fields_mapping.values():
        for num_field in event_num_fields:
            numeric_fields_list.add(num_field)
    Integration.numeric_fields_list = numeric_fields_list

    run_as_service = config.get('run_as_service', False)

    if not run_as_service:
        if 'cron_interval_minutes' in config:
            cron_interval = config['cron_interval_minutes']
        else:
            cron_interval = int(getenv("CRON_INTERVAL_MINUTES", 60))

        integration = Integration(config, event_mapping, cron_interval)
        integration.run()
    else:
        service_schedule = config.get('service_schedule')
        service_hour = service_schedule['hour']
        service_minute = service_schedule['minute']
        integration = Integration(config, event_mapping, 0)
        jobstores = {
            'default': MemoryJobStore(),
        }
        executors = {
            'default': ThreadPoolExecutor(20),
        }
        job_defaults = {
            'coalesce': False,
            'max_instances': 3
        }
        scheduler = BlockingScheduler(jobstores=jobstores, executors=executors, job_defaults=job_defaults, timezone=utc)
        scheduler.add_job(integration.run, trigger='cron', hour=service_hour, minute=service_minute, second='0')

        print_info('Press Ctrl+{0} to exit'.format('Break' if os.name == 'nt' else 'C'))
        scheduler.start()

def load_config(config_file: str):
    with open(config_file) as stream:
        config = load(stream, Loader=Loader)
    new_queries = []
    if 'queries' in config:
        for query in config['queries']:
            if type(query) is str:
                with open(query) as stream:
                    sub_query_config = load(stream, Loader=Loader)
                if 'queries' in sub_query_config and type(sub_query_config['queries']) is list:
                    new_queries = new_queries + sub_query_config['queries']
                else:
                    print_warn("Malformed subconfig file. Ignoring")
            elif type(query) is dict:
                new_queries.append(query)
            else:
                print_warn("Malformed 'queries' member in config, expected either dictionaries or strings in the array. Ignoring.")
                pass
    config['queries'] = new_queries
    return config

if __name__ == "__main__":
    main()
    print_info("Integration end.")
