from .http_session import new_retry_session
from .newrelic import NewRelic
from .salesforce import SalesForce


class Integration:

    def __init__(self, config, event_type_fields_mapping, initial_delay):
        self.instances = []
        for instance in config['instances']:
            labels = instance['labels']
            client = SalesForce(instance['arguments'], event_type_fields_mapping, initial_delay)
            self.instances.append({'labels': labels, 'client': client})
        newrelic_config = config['newrelic']
        NewRelic.license_key = newrelic_config['license_key']
        api_endpoint = newrelic_config['http_endpoint']
        if api_endpoint == "US":
            NewRelic.api_endpoint = NewRelic.US_LOGGING_ENDPOINT
        elif api_endpoint == "EU":
            NewRelic.api_endpoint = NewRelic.EU_LOGGING_ENDPOINT
        else:
            NewRelic.api_endpoint = newrelic_config['http_endpoint']

    def run(self):
        sfdc_session = new_retry_session()
        nr_session = new_retry_session()
        for instance in self.instances:
            labels = instance['labels']
            client = instance['client']

            if not client.authenticate(sfdc_session):
                print(f"error authenticating with {client.token_url}")
                continue

            logs = client.fetch_logs(sfdc_session)
            for data in logs:
                rows = data['rows']
                if len(rows) == 0:
                    continue

                payload = [{'common': labels, 'logs': rows}]
                log_type = data['log_type']
                log_file_id = data['Id']

                status_code = NewRelic.post(nr_session, payload)
                if status_code != 202:
                    print(f'newrelic logs api  returned code- {status_code}')
                else:
                    print(f"sent {len(rows)} log messages from log file {log_type}/{log_file_id}")
