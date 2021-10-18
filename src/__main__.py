#!/usr/bin/env python
import os
import sys
import getopt

from apscheduler.executors.pool import ThreadPoolExecutor
from apscheduler.jobstores.memory import MemoryJobStore
from apscheduler.schedulers.background import BlockingScheduler
from pytz import utc
from yaml import Loader, load

from newrelic_logging.integration import Integration

config_dir = None
argv = sys.argv[1:]
try:
    opts, args = getopt.getopt(argv, 'c:', ['config_dir='])
    for opt, arg in opts:
        if opt in ('-c', '--config_dir'):
            config_dir = arg

except getopt.GetoptError:
    sys.exit(f'error parsing command line options')

if config_dir is None:
    config_dir = os.environ.get('CONFIG_DIR')
    if config_dir is None:
        config_dir = os.getcwd()

config_file = f'{config_dir}/config.yml'

if not os.path.exists(config_file):
    sys.exit(f'config file {config_file} not found')

event_mapping_file = f'{config_dir}/event_type_fields.yml'


def main():
    with open(config_file) as stream:
        config = load(stream, Loader=Loader)

    if not os.path.exists(event_mapping_file):
        print(f'event_mapping_file {event_mapping_file} not found, so event mapping will not be used', file=sys.stderr)
        event_mapping = {}
    else:
        with open(event_mapping_file) as stream:
            event_mapping = load(stream, Loader=Loader)['mapping']

    run_as_service = config.get('run_as_service', False)

    if not run_as_service:
        cron_interval = config.get('cron_interval_minutes', 60)
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
        scheduler.start()
        print('Press Ctrl+{0} to exit'.format('Break' if os.name == 'nt' else 'C'))


if __name__ == "__main__":
    main()
