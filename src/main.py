#!/usr/bin/env python
import os
import sys

from apscheduler.executors.pool import ThreadPoolExecutor
from apscheduler.jobstores.memory import MemoryJobStore
from apscheduler.schedulers.background import BlockingScheduler
from pytz import utc
from yaml import Loader, load

from newrelic_logging.integration import Integration

if __name__ == "__main__":
    config_file = f'{os.getcwd()}/config.yml'
    print(config_file)
    if not os.path.exists(config_file):
        sys.exit(f'config file [{config_file}] not found')
    event_mapping_file = f'{os.getcwd()}/event_type_fields.yml'
    with open(config_file) as stream:
        config = load(stream, Loader=Loader)
    with open(event_mapping_file) as stream:
        event_type_fields_mapping = load(stream, Loader=Loader)['mapping']

    integration = Integration(config, event_type_fields_mapping)

    jobstores = {
        'mongo': MemoryJobStore(),
    }
    executors = {
        'default': ThreadPoolExecutor(20),
    }
    job_defaults = {
        'coalesce': False,
        'max_instances': 3
    }
    scheduler = BlockingScheduler(jobstores=jobstores, executors=executors, job_defaults=job_defaults, timezone=utc)
    # scheduler.add_job(integration.run, trigger='cron', hour="*", minute='5,15,25,35,45,55', second='30')
    scheduler.add_job(integration.run, trigger='cron', hour="*", minute='*', second='30')
    scheduler.start()
    print('Press Ctrl+{0} to exit'.format('Break' if os.name == 'nt' else 'C'))

