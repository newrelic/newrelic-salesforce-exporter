import sys

from .http_session import new_retry_session
from .newrelic import NewRelic
from .salesforce import SalesForce
from enum import Enum


class DataFormat(Enum):
    LOGS = 1
    EVENTS = 2


class Integration:
    numeric_fields_list = set()

    def __init__(self, config, event_type_fields_mapping, initial_delay):
        self.instances = []
        for instance in config['instances']:
            labels = instance['labels']
            labels['nr-labs'] = 'data'
            client = SalesForce(instance['arguments'], event_type_fields_mapping, initial_delay)
            oauth_type = instance['arguments']['auth']['grant_type']
            self.instances.append({'labels': labels, 'client': client, "oauth_type": oauth_type})
        newrelic_config = config['newrelic']
        data_format = newrelic_config['data_format']
        if data_format.lower() == "logs":
            self.data_format = DataFormat.LOGS
            NewRelic.logs_license_key = newrelic_config['license_key']
            NewRelic.set_logs_endpoint(newrelic_config['http_endpoint'])
        elif data_format.lower() == "events":
            self.data_format = DataFormat.EVENTS
            NewRelic.events_api_key = newrelic_config['license_key']
            NewRelic.set_api_endpoint(newrelic_config['api_endpoint'], newrelic_config['account_id'])
        else:
            sys.exit(f'invalid data_format specified. valid values are "logs" or "events"')

    def run(self):
        sfdc_session = new_retry_session()

        for instance in self.instances:
            labels = instance['labels']
            client = instance['client']
            oauth_type = instance['oauth_type']

            if oauth_type == 'password':
                if not client.authenticate_with_password(sfdc_session):
                    print(f"error authenticating with {client.token_url}")
                    continue
            else:
                if not client.authenticate_with_jwt(sfdc_session):
                    print(f"error authenticating with {client.token_url}")
                    continue

            logs = client.fetch_logs(sfdc_session)
            if self.data_format == DataFormat.LOGS:
                self.process_logs(logs, labels)
            else:
                self.process_events(logs, labels)

    @staticmethod
    def process_logs(logs, labels):
        nr_session = new_retry_session()
        for log_file_obj in logs:
            log_entries = log_file_obj['log_entries']
            if len(log_entries) == 0:
                continue

            payload = [{'common': labels, 'logs': log_entries}]
            log_type = log_file_obj['log_type']
            log_file_id = log_file_obj['Id']

            status_code = NewRelic.post_logs(nr_session, payload)
            if status_code != 202:
                print(f'newrelic logs api returned code- {status_code}')
            else:
                print(f"sent {len(log_entries)} log messages from log file {log_type}/{log_file_id}")

    @staticmethod
    def process_events(logs, labels):
        nr_session = new_retry_session()
        for log_file_obj in logs:
            log_entries = log_file_obj['log_entries']
            if len(log_entries) == 0:
                continue
            log_events = []
            for log_entry in log_entries:
                log_event = {}
                message = log_entry['message']
                for event_name in message:
                    event_value = message[event_name]
                    if event_name in Integration.numeric_fields_list:
                        if event_value:
                            try:
                                log_event[event_name] = int(event_value)
                            except (TypeError, ValueError) as e:
                                print(f'error for {event_name} / {event_value}')
                                try:
                                    log_event[event_name] = float(event_value)
                                except (TypeError, ValueError) as e:
                                    log_event[event_name] = event_value
                        else:
                            log_event[event_name] = 0
                    else:
                        log_event[event_name] = event_value
                log_event.update(labels)
                event_type = log_event.get('EVENT_TYPE')
                if event_type is None:
                    continue
                log_event['eventType'] = 's' + event_type
                log_events.append(log_event)
                print(log_event)
                print('\n')
            if len(log_entries) > 2000:
                # TODO: split payload into multiple
                print("skipping as there are more than 2000 events for payload from log file {log_type}/{log_file_id}")
                continue

            log_type = log_file_obj['log_type']
            log_file_id = log_file_obj['Id']

            status_code = NewRelic.post_events(nr_session, log_events)
            if status_code != 200:
                print(f'newrelic events api returned code- {status_code}')
            else:
                print(f"posted {len(log_events)} events from log file {log_type}/{log_file_id}")
