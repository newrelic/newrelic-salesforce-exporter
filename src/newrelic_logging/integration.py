import sys
from .http_session import new_retry_session
from .newrelic import NewRelic
from .salesforce import SalesForce, SalesforceApiException, DataCache
from .auth_env import AuthEnv
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
            #TODO: get general api_ver that applies to all queries of one instance
            prefix = instance['arguments'].get('auth_env_prefix', '')
            auth_env = AuthEnv(prefix)
            #TODO: move queries to the instance level, so we can have different queries for each instance.
            #TODO: also keep general queries that apply to all instances.
            if 'queries' in config:
                client = SalesForce(auth_env, instance_name, instance['arguments'], event_type_fields_mapping, initial_delay, config['queries'])
            else:
                client = SalesForce(auth_env, instance_name, instance['arguments'], event_type_fields_mapping, initial_delay)
            if 'auth' in instance['arguments']:
                if 'grant_type' in instance['arguments']['auth']:
                    oauth_type = instance['arguments']['auth']['grant_type']
                else:
                    sys.exit("No 'grant_type' specified under 'auth' section in config.yml for instance '" + instance_name + "'")
            else:
                oauth_type = auth_env.get_grant_type('')
            self.instances.append({'labels': labels, 'client': client, "oauth_type": oauth_type, 'name': instance_name})
        newrelic_config = config['newrelic']
        data_format = newrelic_config['data_format']
        auth_env = AuthEnv('')
        if data_format.lower() == "logs":
            self.data_format = DataFormat.LOGS
            if 'license_key' in newrelic_config:
                NewRelic.logs_license_key = newrelic_config['license_key']
            else:
                NewRelic.logs_license_key = auth_env.get_license_key()
            NewRelic.set_logs_endpoint(newrelic_config['api_endpoint'])
        elif data_format.lower() == "events":
            self.data_format = DataFormat.EVENTS
            if 'license_key' in newrelic_config:
                NewRelic.events_api_key = newrelic_config['license_key']
            else:
                NewRelic.events_api_key = auth_env.get_license_key()
            if 'account_id' in newrelic_config:
                account_id = newrelic_config['account_id']
            else:
                account_id = auth_env.get_account_id()
            NewRelic.set_api_endpoint(newrelic_config['api_endpoint'], account_id)
        else:
            sys.exit(f'invalid data_format specified. valid values are "logs" or "events"')

    def run(self):
        sfdc_session = new_retry_session()

        for instance in self.instances:
            print("Running instance '" + instance['name'] + "'")

            labels = instance['labels']
            client = instance['client']
            oauth_type = instance['oauth_type']
            
            logs = self.auth_and_fetch(True, client, oauth_type, sfdc_session)
            if self.response_empty(logs):
                print("------ NO DATA TO BE SENT ------")
                continue

            if self.data_format == DataFormat.LOGS:
                self.process_logs(logs, labels, client.data_cache)
            else:
                self.process_events(logs, labels, client.data_cache)

    def auth_and_fetch(self, retry, client, oauth_type, sfdc_session):
        if not client.authenticate(oauth_type, sfdc_session):
            return None
        
        logs = None
        try:
            logs = client.fetch_logs(sfdc_session)
        except SalesforceApiException as e:
            if e.err_code == 401:
                if retry:
                    print("-----> Invalid token, retry auth and fetch...")
                    client.clear_auth()
                    return self.auth_and_fetch(False, client, oauth_type, sfdc_session)
                else:
                    print("Exception while fetching data from SF: ", e)
                    return None
            else:
                print("Exception while fetching data from SF: ", e)
                return None
        except Exception as e:
            print("Exception while fetching data from SF: ", e)
            return None
        
        return logs
    
    @staticmethod
    def response_empty(logs):
        return logs == None or (len(logs) == 1 and len(logs[0].get("log_entries", [])) == 0)
    
    @staticmethod
    def cache_processed_data(log_file_id, log_entries, data_cache: DataCache):
        if data_cache.redis:
            if log_file_id == '':
                # Events
                for log in log_entries:
                    log_id = log.get('attributes', {}).get('Id', '')
                    print(f"---> ID OF EVENT = {log_id}")
                    data_cache.persist_event(log_id)
            else:
                # Logs
                print(f"---> ID OF LOG FILE = {log_file_id}")
                data_cache.persist_logs(log_file_id)
    
    @staticmethod
    def process_logs(logs, labels, data_cache: DataCache):
        nr_session = new_retry_session()
        for log_file_obj in logs:
            log_entries = log_file_obj['log_entries']
            if len(log_entries) == 0:
                continue

            payload = [{'common': labels, 'logs': log_entries}]
            log_type = log_file_obj.get('log_type', '')
            log_file_id = log_file_obj.get('Id', '')
            
            status_code = NewRelic.post_logs(nr_session, payload)
            if status_code != 202:
                print(f'newrelic logs api returned code- {status_code}')
            else:
                print(f"sent {len(log_entries)} log messages from log file {log_type}/{log_file_id}")
                Integration.cache_processed_data(log_file_id, log_entries, data_cache)

    @staticmethod
    def process_events(logs, labels, data_cache: DataCache):
        nr_session = new_retry_session()
        for log_file_obj in logs:
            log_file_id = log_file_obj.get('Id', '')
            log_entries = log_file_obj['log_entries']
            if len(log_entries) == 0:
                continue
            log_events = []
            for log_entry in log_entries:
                log_event = {}
                attributes = log_entry['attributes']
                for event_name in attributes:
                    # currently no need to modify as we did not see any special chars that need to be removed
                    modified_event_name = event_name
                    event_value = attributes[event_name]
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
                event_type = log_event.get('EVENT_TYPE', "UnknownSFEvent")
                log_event['eventType'] = event_type
                log_events.append(log_event)

            # NOTE: this is probably unnecessary now, because we already have a slicing method with a limit of 1000 in SalesForce.extract_row_slice
            # since the max number of events that can be posted in a single payload to New Relic is 2000
            max_events = 2000
            x = [log_events[i:i + max_events] for i in range(0, len(log_events), max_events)]

            for log_entries_slice in x:
                status_code = NewRelic.post_events(nr_session, log_entries_slice)
                if status_code != 200:
                    print(f'newrelic events api returned code- {status_code}')
                else:
                    log_type = log_file_obj.get('log_type', '')
                    log_file_id = log_file_obj.get('Id', '')
                    print(f"posted {len(log_entries_slice)} events from log file {log_type}/{log_file_id}")
                    Integration.cache_processed_data(log_file_id, log_entries, data_cache)
