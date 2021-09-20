import csv
from datetime import datetime, timedelta

import pytz
import redis
import requests


class NotConnectedException(Exception):
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

    def set_redis(self, client):
        self.redis = client

    def get_access_token(self):
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
        r = requests.post(self.token_url, params=params,
                          headers=headers)
        if r.status_code != 200:
            return False

        ret = r.json()
        self.access_token = ret['access_token']
        self.instance_url = ret['instance_url']
        self.token_type = ret['token_type']
        return True

    def request(self, url, data={}, headers={}, method='get'):
        if not self.access_token:
            raise NotConnectedException("You must first get an access_token")

        f = getattr(requests, method)

        h = {
            'Authorization': f'Bearer {self.access_token}'
        }
        h.update(headers)

        return f(url, data=data, headers=h)

    def fetch_logs(self):

        to_timestamp = (datetime.utcnow() - timedelta(minutes=self.time_lag_minutes)).isoformat(
            timespec='milliseconds') + "Z"
        from_timestamp = self.last_to_timestamp
        self.last_to_timestamp = to_timestamp

        query = self.query_template.format(to_timestamp=to_timestamp, from_timestamp=from_timestamp,
                                           log_interval_type=self.generation_interval)
        print(f'Running query {query}')

        url = f'{self.instance_url}/services/data/v52.0/query?q={query}'

        ret = self.request(url).json()

        logs = []
        for i in ret['records']:
            log_type = i['EventType']
            log_file_id = i['Id']
            cache_key = f'{log_file_id}'
            if self.redis:
                cache_key_exists = self.redis.exists(cache_key)
                if cache_key_exists:
                    cached_messages = self.redis.lrange(cache_key, 0, -1)
                else:
                    cache_key_exists = False
                    self.redis.rpush(cache_key, '')
                    self.redis.expire(cache_key, timedelta(days=7))

            content = self.download(i['LogFile']).decode('utf-8')
            reader = csv.DictReader(content.splitlines())
            rows = []
            for row in reader:
                row_id = row["REQUEST_ID"]
                message = {}
                if self.redis:
                    if cache_key_exists:
                        if row_id in cached_messages:
                            continue
                    self.redis.rpush("cache_key", row_id)

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
        return logs

    def download(self, path):

        return self.request(f'{self.instance_url}{path}').content
