import redis
from datetime import timedelta

from .config import Config
from .telemetry import print_err, print_info


CONFIG_CACHE_ENABLED = 'cache_enabled'
CONFIG_REDIS_HOST = 'redis.host'
CONFIG_REDIS_PORT = 'redis.port'
CONFIG_REDIS_DB_NUMBER = 'redis.db_number'
CONFIG_REDIS_PASSWORD = 'redis.password'
CONFIG_REDIS_USE_SSL = 'redis.ssl'
CONFIG_REDIS_EXPIRE_DAYS = 'redis.expire_days'
DEFAULT_CACHE_ENABLED = False
DEFAULT_REDIS_HOST = 'localhost'
DEFAULT_REDIS_PORT = 6379
DEFAULT_REDIS_DB_NUMBER = 0
DEFAULT_REDIS_EXPIRE_DAYS = 2
DEFAULT_REDIS_SSL = False


# Local cache, to store data before sending it to Redis.
class DataCache:
    redis = None
    redis_expire = None
    cached_events = {}
    cached_logs = {}

    def __init__(self, redis, redis_expire) -> None:
        self.redis = redis
        self.redis_expire = redis_expire

    def set_redis_expire(self, key):
        try:
            self.redis.expire(key, timedelta(days=self.redis_expire))
        except Exception as e:
            print_err(f"Failed setting expire time for key {key}: {e}")
            exit(1)

    def persist_logs(self, record_id: str) -> bool:
        if record_id in self.cached_logs:
            for row_id in self.cached_logs[record_id]:
                try:
                    self.redis.rpush(record_id, row_id)
                except Exception as e:
                    print_err(f"Failed pushing record {record_id}: {e}")
                    exit(1)
                # Set expire date for the whole list only once, when it find the first entry ('init')
                if row_id == 'init':
                    self.set_redis_expire(record_id)
            del self.cached_logs[record_id]
            return True
        else:
            return False

    def persist_event(self, record_id: str) -> bool:
        if record_id in self.cached_events:
            try:
                self.redis.set(record_id, '')
            except Exception as e:
                print_err(f"Failed setting record {record_id}: {e}")
                exit(1)
            self.set_redis_expire(record_id)
            del self.cached_events[record_id]
            return True
        else:
            return False

    def can_skip_downloading_record(self, record_id: str) -> bool:
        try:
            does_exist = self.redis.exists(record_id)
        except Exception as e:
            print_err(f"Failed checking record {record_id}: {e}")
            exit(1)
        if does_exist:
            try:
                return self.redis.llen(record_id) > 1
            except Exception as e:
                print_err(f"Failed checking len for record {record_id}: {e}")
                exit(1)

        return False

    def retrieve_cached_message_list(self, record_id: str):
        try:
            cache_key_exists = self.redis.exists(record_id)
        except Exception as e:
            print_err(f"Failed checking record {record_id}: {e}")
            exit(1)

        if cache_key_exists:
            try:
                cached_messages = self.redis.lrange(record_id, 0, -1)
            except Exception as e:
                print_err(f"Failed getting list range for record {record_id}: {e}")
                exit(1)
            return cached_messages
        else:
            self.cached_logs[record_id] = ['init']

        return None

    # Cache event
    def check_cached_id(self, record_id: str):
        try:
            does_exist = self.redis.exists(record_id)
        except Exception as e:
            print_err(f"Failed checking record {record_id}: {e}")
            exit(1)

        if does_exist:
            return True
        else:
            self.cached_events[record_id] = ''
            return False

    # Cache log
    def record_or_skip_row(self, record_id: str, row: dict, cached_messages: dict) -> bool:
        row_id = row["REQUEST_ID"]

        if cached_messages is not None:
            row_id_b = row_id.encode('utf-8')
            if row_id_b in cached_messages:
                return True
            self.cached_logs[record_id].append(row_id)
        else:
            self.cached_logs[record_id].append(row_id)

        return False


def make_cache(config: Config):
    if config.get_bool(CONFIG_CACHE_ENABLED, DEFAULT_CACHE_ENABLED):
        host = config.get(CONFIG_REDIS_HOST, DEFAULT_REDIS_HOST)
        port = config.get_int(CONFIG_REDIS_PORT, DEFAULT_REDIS_PORT)
        db = config.get_int(CONFIG_REDIS_DB_NUMBER, DEFAULT_REDIS_DB_NUMBER)
        password = config.get(CONFIG_REDIS_PASSWORD)
        ssl = config.get_bool(CONFIG_REDIS_USE_SSL, DEFAULT_REDIS_SSL)
        expire_days = config.get_int(CONFIG_REDIS_EXPIRE_DAYS)
        password_display = "XXXXXX" if password != None else None

        print_info(
            f'cache enabled, connecting to redis instance {host}:{port}:{db}, ssl={ssl}, password={password_display}'
        )

        return DataCache(redis.Redis(
            host=host,
            port=port,
            db=db,
            password=password,
            ssl=ssl
        ), expire_days)

    print_info('cache disabled')

    return None
