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
            instance_name = instance['name']
            labels = instance['labels']
            labels['nr-labs'] = 'data'
            if 'queries' in config:
                client = SalesForce(instance_name, instance['arguments'], event_type_fields_mapping, initial_delay, config['queries'])
            else:
                client = SalesForce(instance_name, instance['arguments'], event_type_fields_mapping, initial_delay)
            oauth_type = instance['arguments']['auth']['grant_type']
            self.instances.append({'labels': labels, 'client': client, "oauth_type": oauth_type})
        newrelic_config = config['newrelic']
        data_format = newrelic_config['data_format']
        if data_format.lower() == "logs":
            self.data_format = DataFormat.LOGS
            NewRelic.logs_license_key = newrelic_config['license_key']
            NewRelic.set_logs_endpoint(newrelic_config['api_endpoint'])
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
                    # currently no need to modify as we did not see any special chars that need to be removed
                    modified_event_name = event_name
                    event_value = message[event_name]
                    if event_name in Integration.numeric_fields_list:
                        if event_value:
                            try:
                                log_event[modified_event_name] = int(event_value)
                            except (TypeError, ValueError) as e:
                                try:
                                    log_event[modified_event_name] = float(event_value)
                                except (TypeError, ValueError) as e:
                                    print(f'type conversion error for {event_name}[{event_value}]')
                                    log_event[modified_event_name] = event_value
                        else:
                            log_event[modified_event_name] = 0
                    else:
                        log_event[modified_event_name] = event_value
                log_event.update(labels)
                event_type = log_event.get('EVENT_TYPE')
                if event_type is None:
                    print(f'EVENT_TYPE attribute could not be extracted. Unable to process event.')
                    continue
                log_event['eventType'] = event_type
                log_events.append(log_event)

            # since the max number of events that can be posted in a single payload to New Relic is 2000
            max_events = 2000
            x = [log_events[i:i + max_events] for i in range(0, len(log_events), max_events)]

            for log_entries_slice in x:
                status_code = NewRelic.post_events(nr_session, log_entries_slice)
                if status_code != 200:
                    print(f'newrelic events api returned code- {status_code}')
                else:
                    log_type = log_file_obj['log_type']
                    log_file_id = log_file_obj['Id']
                    print(f"posted {len(log_entries_slice)} events from log file {log_type}/{log_file_id}")
