import base64
import csv
import json
import sys
from datetime import datetime, timedelta
import jwt
from cryptography.hazmat.primitives import serialization

import pytz
import redis
from requests import RequestException


class LoginException(Exception):
    pass


class SalesforceApiException(Exception):
    pass


SALESFORCE_CREATED_DATE_QUERY = \
    "SELECT+Id,+EventType,+CreatedDate,+LogDate,+Interval,+LogFile,+Sequence+From+EventLogFile+Where+CreatedDate>={" \
    "from_timestamp}+AND+CreatedDate<{to_timestamp}+AND+Interval='{log_interval_type}' "
SALESFORCE_LOG_DATE_QUERY = \
    "SELECT+Id,+EventType,+CreatedDate,+LogDate,+Interval,+LogFile,+Sequence+From+EventLogFile+Where+LogDate>={" \
    "from_timestamp}+AND+LogDate<{to_timestamp}+AND+Interval='{log_interval_type}' "


def base64_url_encode(json_obj):
    json_str = json.dumps(json_obj)
    encoded_bytes = base64.urlsafe_b64encode(json_str.encode('utf-8'))
    encoded_str = str(encoded_bytes, 'utf-8')
    return encoded_str


class SalesForce:
    access_token = None
    instance_url = None
    token_type = None
    token_url = ''
    redis = False

    def __init__(self, instance_name, config, event_type_fields_mapping, initial_delay, queries=[]):
        self.instance_name = instance_name
        try:
            self.auth_data = config['auth']
            self.token_url = config['token_url']
            self.time_lag_minutes = config['time_lag_minutes']
            self.generation_interval = config['generation_interval']
            self.date_field = config['date_field']
            self.cache_enabled = config['cache_enabled']
        except KeyError as e:
            print(f'Please specify a "{e.args[0]}" parameter for sfdc instance "{instance_name}" in config.yml')
            sys.exit(1)

        if self.cache_enabled:
            try:
                redis_config = config['redis']
            except KeyError as e:
                print(f'Please specify a "{e.args[0]}" parameter for sfdc instance "{instance_name}" in config.yml')
                sys.exit(1)

        self.last_to_timestamp = (datetime.utcnow() - timedelta(
            minutes=self.time_lag_minutes + initial_delay)).isoformat(timespec='milliseconds') + "Z"

        if len(queries) > 0:
            self.query_template = queries
        else:
            if self.date_field.lower() == "logdate":
                self.query_template = SALESFORCE_LOG_DATE_QUERY
            else:
                self.query_template = SALESFORCE_CREATED_DATE_QUERY
        
        if self.cache_enabled:
            r = redis.Redis(host=redis_config['host'], port=redis_config['port'], db=redis_config['db_number'],
                            password=redis_config['password'],
                            ssl=True)
            self.set_redis(r)
        self.event_type_fields_mapping = event_type_fields_mapping
        self.authenticated = False

    def set_redis(self, client):
        self.redis = client

    def is_authenticated(self):
        return self.authenticated

    def authenticate_with_jwt(self, session):
        try:
            private_key_file = self.auth_data['private_key']
            client_id = self.auth_data['client_id']
            subject = self.auth_data['subject']
            audience = self.auth_data['audience']
        except KeyError as e:
            print(f'Please specify a "{e.args[0]}" parameter under "auth" section '
                  'of salesforce instance in config.yml')
            sys.exit(1)

        exp = int((datetime.utcnow() - timedelta(minutes=5)).timestamp())

        private_key = open(private_key_file, 'r').read()
        try:
            key = serialization.load_ssh_private_key(private_key.encode(), password=b'')
        except ValueError as e:
            print(f'authentication failed for {self.instance_name}. error message: {str(e)}')
            return False

        jwt_claim_set = {"iss": client_id,
                         "sub": subject,
                         "aud": audience,
                         "exp": exp}

        signed_token = jwt.encode(
            jwt_claim_set,
            key,
            algorithm='RS256',
        )

        params = {
            "grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer",
            "assertion": signed_token,
            "format": "json"
        }

        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/json"
        }

        try:
            resp = session.post(self.token_url, params=params,
                                headers=headers)
            if resp.status_code != 200:
                error_message = f'sfdc token request failed. http-status-code:{resp.status_code}, reason: {resp.text}'
                print(f'authentication failed for {self.instance_name}. message: {error_message}', file=sys.stderr)
                return False

            resp_json = resp.json()
            self.access_token = resp_json['access_token']
            self.instance_url = resp_json['instance_url']
            self.token_type = resp_json['token_type']
            self.authenticated = True
            return True
        except ConnectionError as e:
            raise LoginException(f'authentication failed for sfdc instance {self.instance_name}') from e
        except RequestException as e:
            raise LoginException(f'authentication failed for sfdc instance {self.instance_name}') from e

    def authenticate_with_password(self, session):
        client_id = self.auth_data['client_id']
        client_secret = self.auth_data['client_secret']
        username = self.auth_data['username']
        password = self.auth_data['password']

        params = {
            "grant_type": "password",
            "client_id": client_id,
            "client_secret": client_secret,
            "username": username,
            "password": password
        }

        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/json"
        }

        try:
            resp = session.post(self.token_url, params=params,
                                headers=headers)
            if resp.status_code != 200:
                error_message = f'salesforce token request failed. status-code:{resp.status_code}, reason: {resp.reason}'
                print(error_message, file=sys.stderr)
                return False

            resp_json = resp.json()
            self.access_token = resp_json['access_token']
            self.instance_url = resp_json['instance_url']
            self.token_type = resp_json['token_type']
            self.authenticated = True
            return True
        except ConnectionError as e:
            raise LoginException(f'authentication failed for sfdc instance {self.instance_name}') from e
        except RequestException as e:
            raise LoginException(f'authentication failed for sfdc instance {self.instance_name}') from e

    def make_multiple_queries(self, query_templates):
        return [self.make_single_query(template) for template in query_templates]

    def make_single_query(self, query_template):
        to_timestamp = (datetime.utcnow() - timedelta(minutes=self.time_lag_minutes)).isoformat(
            timespec='milliseconds') + "Z"
        from_timestamp = self.last_to_timestamp
        self.last_to_timestamp = to_timestamp
        query = query_template.format(to_timestamp=to_timestamp, from_timestamp=from_timestamp,
                                           log_interval_type=self.generation_interval)
        return query

    def execute_query(self, query, session):
        url = f'{self.instance_url}/services/data/v52.0/query?q={query}'

        try:
            headers = {
                'Authorization': f'Bearer {self.access_token}'
            }
            query_response = session.get(url, headers=headers)
            if query_response.status_code != 200:
                error_message = f'salesforce event log query failed. ' \
                                f'status-code:{query_response.status_code}, ' \
                                f'reason: {query_response.reason} ' \
                                f'response: {query_response.text} '

                raise SalesforceApiException(f'error when trying to run SOQL query. message: {error_message}')
            return query_response.json()
        except RequestException as e:
            raise SalesforceApiException(f'error when trying to run SOQL query. cause: {e}') from e

    def retrieve_cached_message_list(self, record_id):
        cache_key_exists = self.redis.exists(record_id)
        if cache_key_exists:
            cached_messages = self.redis.lrange(record_id, 0, -1)
            return cached_messages
        else:
            self.redis.rpush(record_id, 'init')
            self.redis.expire(record_id, timedelta(days=7))
        return None

    def download_file(self, session, url):
        headers = {
            'Authorization': f'Bearer {self.access_token}'
        }
        response = session.get(url, headers=headers)
        if response.status_code != 200:
            error_message = f'salesforce event log file download failed. ' \
                            f'status-code: {response.status_code}, ' \
                            f'reason: {response.reason} ' \
                            f'response: {response.text}'
            print(error_message, file=sys.stderr)
            return None
        return response

    def parse_csv(self, download_response, record_id, record_event_type, cached_messages):
        content = download_response.content.decode('utf-8')
        reader = csv.DictReader(content.splitlines())
        rows = []
        for row in reader:
            row_id = row["REQUEST_ID"]
            if self.redis:
                if cached_messages is not None:
                    row_id_b = row_id.encode('utf-8')
                    if row_id_b in cached_messages:
                        # print(f' debug: dropping message with REQUEST_ID: {row_id}')
                        continue
                    self.redis.rpush(record_id, row_id)
                else:
                    self.redis.rpush(record_id, row_id)
            rows.append(row)
        return rows
    
    def fetch_logs(self, session):
        if type(self.query_template) is list:
            queries = self.make_multiple_queries(self.query_template)
            logs = []
            for query in queries:
                part_logs = self.fetch_logs_from_single_req(session, query)
                logs.extend(part_logs)
            return logs
        else:
            query = self.make_single_query(self.query_template)
            return self.fetch_logs_from_single_req(session, query)

    def fetch_logs_from_single_req(self, session, query):
        logs = []

        try:
            print(f'Running query {query}')
            response = self.execute_query(query, session)
            #UNDO: print
            print("Response = ", response)
        except SalesforceApiException as e:
            print(e, file=sys.stderr)
            return

        for record in response['records']:
            record_file_name = record.get('LogFile', None)
            if record_file_name is None:
                continue

            record_id = str(record['Id'])
            record_event_type = record['EventType']

            cached_messages = None
            if self.redis:
                cached_messages = self.retrieve_cached_message_list(record_id)

            try:
                download_response = self.download_file(session, f'{self.instance_url}{record_file_name}')
                if download_response is None:
                    continue
            except RequestException as e:
                print(f'salesforce event log file "{record_file_name}" download failed')
                print(e)
                continue

            csv_rows = self.parse_csv(download_response, record_id, record_event_type, cached_messages)

            log_entries = []
            for row in csv_rows:
                message = {}
                if record_event_type in self.event_type_fields_mapping:
                    for field in self.event_type_fields_mapping[record_event_type]:
                        message[field] = row[field]
                else:
                    message = row

                if row.get('TIMESTAMP'):
                    timestamp_obj = datetime.strptime(row.get('TIMESTAMP'), '%Y%m%d%H%M%S.%f')
                    timestamp = pytz.utc.localize(timestamp_obj).replace(microsecond=0).timestamp()
                else:
                    timestamp = datetime.utcnow().replace(microsecond=0).timestamp()

                message['LogFileId'] = record_id
                message.pop('TIMESTAMP', None)
                message['timestamp'] = int(timestamp)

                log_entries.append({
                    'message': message,
                    'timestamp': int(timestamp)
                })

            logs.append({
                'log_type': record_event_type,
                'Id': record_id,
                'CreatedDate': record['CreatedDate'],
                'LogDate': record['LogDate'],
                'log_entries': log_entries
            })

        return logs
