import csv
import sys
from datetime import datetime, timedelta

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


class SalesForce:
    access_token = None
    instance_url = None
    token_type = None
    token_url = ''
    redis = False

    def __init__(self, config, event_type_fields_mapping, initial_delay):
        self.client_id = config['auth']['client_id']
        self.client_secret = config['auth']['client_secret']
        self.username = config['auth']['username']
        self.password = config['auth']['password']
        self.token_url = config['token_url']
        self.time_lag_minutes = config['time_lag_minutes']
        self.generation_interval = config['generation_interval']
        self.last_to_timestamp = (datetime.utcnow() - timedelta(
            minutes=self.time_lag_minutes + initial_delay)).isoformat(timespec='milliseconds') + "Z"
        self.date_field = config['date_field']
        if config['date_field'].lower() == "logdate":
            self.query_template = SALESFORCE_LOG_DATE_QUERY
        else:
            self.query_template = SALESFORCE_CREATED_DATE_QUERY
        if config['cache_enabled']:
            redis_config = config['redis']
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

    def authenticate(self, session):
        params = {
            "grant_type": "password",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "username": self.username,
            "password": self.password
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
            raise LoginException(f'salesforce authentication failed') from e
        except RequestException as e:
            raise LoginException(f'salesforce authentication failed') from e

    def fetch_logs(self, session):
        to_timestamp = (datetime.utcnow() - timedelta(minutes=self.time_lag_minutes)).isoformat(
            timespec='milliseconds') + "Z"
        from_timestamp = self.last_to_timestamp
        self.last_to_timestamp = to_timestamp
        query = self.query_template.format(to_timestamp=to_timestamp, from_timestamp=from_timestamp,
                                           log_interval_type=self.generation_interval)
        print(f'Running query {query}')

        url = f'{self.instance_url}/services/data/v52.0/query?q={query}'

        try:
            headers = {
                'Authorization': f'Bearer {self.access_token}'
            }
            soql_response = session.get(url, headers=headers)
            if soql_response.status_code != 200:
                error_message = f'salesforce event log query failed. ' \
                                f'status-code:{soql_response.status_code}, ' \
                                f'reason: {soql_response.reason} ' \
                                f'response: {soql_response.text} '
                print(error_message, file=sys.stderr)
                return
        except RequestException as e:
            raise SalesforceApiException('error when trying to run SOQL query. cause: {e}') from e

        logs = []
        resp_json = soql_response.json()
        for i in resp_json['records']:
            log_type = i['EventType']
            log_file_id = i['Id']
            cache_key = f'{log_file_id}'

            cache_key_exists = False
            cached_messages = None
            if self.redis:
                cache_key_exists = self.redis.exists(cache_key)
                if cache_key_exists:
                    cached_messages = self.redis.lrange(cache_key, 0, -1)
                else:
                    self.redis.rpush(cache_key, 'init')
                    self.redis.expire(cache_key, timedelta(days=7))

            try:
                file_id = i.get('LogFile', None)
                download_response = session.get(f'{self.instance_url}{file_id}', headers=headers)
                if download_response.status_code != 200:
                    error_message = f'salesforce event log file download failed. ' \
                                    f'status-code: {download_response.status_code}, ' \
                                    f'reason: {download_response.reason} ' \
                                    f'response: {download_response.text}'
                    print(error_message, file=sys.stderr)
                    continue
                else:
                    content = download_response.content.decode('utf-8')
                    reader = csv.DictReader(content.splitlines())
                    rows = []
                    for row in reader:
                        row_id = row["REQUEST_ID"]
                        message = {}
                        if self.redis:
                            if cache_key_exists:
                                row_id_b = row_id.encode('utf-8')
                                if row_id_b in cached_messages:
                                    # print('dropping row: cache{row_id}')
                                    continue
                                self.redis.rpush(cache_key, row_id)
                            else:
                                self.redis.rpush(cache_key, row_id)

                        if log_type in self.event_type_fields_mapping:
                            for field in self.event_type_fields_mapping[log_type]:
                                message[field] = row[field]
                        else:
                            message = row

                        if row.get('TIMESTAMP'):
                            timestamp_obj = datetime.strptime(row.get('TIMESTAMP'), '%Y%m%d%H%M%S.%f')
                            timestamp = pytz.utc.localize(timestamp_obj).replace(microsecond=0).timestamp()
                        else:
                            timestamp = datetime.utcnow().replace(microsecond=0).timestamp()

                        message['LogFileId'] = log_file_id
                        rows.append({
                            'message': message,
                            'timestamp': int(timestamp)
                        })
                    logs.append({
                        'log_type': log_type,
                        'Id': log_file_id,
                        'CreatedDate': i['CreatedDate'],
                        'LogDate': i['LogDate'],
                        'rows': rows
                    })
            except RequestException as e:
                raise SalesforceApiException('salesforce event log file download failed') from e
                continue

        return logs
