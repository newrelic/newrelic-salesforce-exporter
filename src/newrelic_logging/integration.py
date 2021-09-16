from .newrelic import NewRelic
from .salesforce import SalesForce


class Integration:

    def __init__(self, config, event_type_fields_mapping):
        self.instances = []
        for instance in config['instances']:
            labels = instance['labels']
            client = SalesForce(instance['arguments'], event_type_fields_mapping)
            if not client.get_access_token():
                print("could not connect to salesforce")
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
        for instance in self.instances:
            labels = instance['labels']
            client = instance['client']
            logs = client.fetch_logs()

            for data in logs:
                rows = data['rows']
                if len(rows) == 0:
                    continue

                payload = [{'common': labels, 'logs': rows}]
                log_type = data['log_type']
                log_file_id = data['Id']

                # BEGIN DEBUG CODE
                #
                # timestamp = int(datetime.utcnow().timestamp())
                # logs_dir = f'logs/{log_type}/'
                # if not os.path.exists(logs_dir):
                #     os.makedirs(logs_dir)
                #
                # logs_dir = f'logs/{log_type}/{timestamp}'
                # if not os.path.exists(logs_dir):
                #     os.makedirs(logs_dir)
                #
                # with open(f'{logs_dir}/{log_file_id}.json', 'w') as f:
                #     f.write(json.dumps(payload, indent=2))
                # END DEBUG CODE

                status_code = NewRelic.post(payload)
                if status_code != 202:
                    print(f'NewRelic logs endpoint returned code- {status_code}')
                else:
                    print(f"Sent {len(rows)} log messages for log file {log_type}/{log_file_id}")
