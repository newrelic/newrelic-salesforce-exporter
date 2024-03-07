import gc
import redis
from datetime import timedelta

from . import CacheException
from .config import Config
from .telemetry import print_info


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


class RedisBackend:
    def __init__(self, redis):
        self.redis = redis

    def exists(self, key):
        return self.redis.exists(key)

    def put(self, key, item):
        self.redis.set(key, item)

    def list_length(self, key):
        return self.redis.llen(key)

    def list_slice(self, key, start, end):
        return self.redis.lrange(key, start, end)

    def list_append(self, key, item):
        self.redis.rpush(key, item)

    def set_expiry(self, key, days):
        self.redis.expire(key, timedelta(days=days))


class DataCache:
    def __init__(self, backend, expiry):
        self.backend = backend
        self.expiry = expiry
        self.cached_events = {}
        self.cached_logs = {}

    def can_skip_downloading_logfile(self, record_id: str) -> bool:
        try:
            return self.backend.exists(record_id) and \
                self.backend.list_length(record_id) > 1
        except Exception as e:
            raise CacheException(f'failed checking record {record_id}: {e}')

    def load_cached_log_lines(self, record_id: str) -> None:
        try:
            if self.backend.exists(record_id):
                    self.cached_logs[record_id] = \
                        self.backend.list_slice(record_id, 0, -1)
                    return

            self.cached_logs[record_id] = ['init']
        except Exception as e:
            raise CacheException(f'failed checking log record {record_id}: {e}')

    # Cache log
    def check_and_set_log_line(self, record_id: str, row: dict) -> bool:
        row_id = row["REQUEST_ID"]

        row_id_b = row_id.encode('utf-8')
        if row_id_b in self.cached_logs[record_id]:
            return True

        self.cached_logs[record_id].append(row_id)

        return False

    # Cache event
    def check_and_set_event_id(self, record_id: str) -> bool:
        try:
            if self.backend.exists(record_id):
                return True

            self.cached_events[record_id] = ''

            return False
        except Exception as e:
            raise CacheException(f'failed checking record {record_id}: {e}')

    def flush(self) -> None:
        # Flush cached log line ids for each log record
        for record_id in self.cached_logs:
            for row_id in self.cached_logs[record_id]:
                try:
                    self.backend.list_append(record_id, row_id)

                    # Set expire date for the whole list only once, when we find
                    # the first entry ('init')
                    if row_id == 'init':
                        self.backend.set_expiry(record_id, self.expiry)
                except Exception as e:
                    raise CacheException(
                        f'failed pushing row {row_id} for record {record_id}: {e}'
                    )

        # Attempt to release memory
        del self.cached_logs[record_id]

        # Flush any cached event record ids
        for record_id in self.cached_events:
            try:
                self.backend.put(record_id, '')
                self.backend.set_expiry(record_id, self.expiry)

                # Attempt to release memory
                del self.cached_events[record_id]
            except Exception as e:
                raise CacheException(f"failed setting record {record_id}: {e}")

        # Run a gc in an attempt to reclaim memory
        gc.collect()


def New(config: Config):
    if config.get_bool(CONFIG_CACHE_ENABLED, DEFAULT_CACHE_ENABLED):
        host = config.get(CONFIG_REDIS_HOST, DEFAULT_REDIS_HOST)
        port = config.get_int(CONFIG_REDIS_PORT, DEFAULT_REDIS_PORT)
        db = config.get_int(CONFIG_REDIS_DB_NUMBER, DEFAULT_REDIS_DB_NUMBER)
        password = config.get(CONFIG_REDIS_PASSWORD)
        ssl = config.get_bool(CONFIG_REDIS_USE_SSL, DEFAULT_REDIS_SSL)
        expire_days = config.get_int(CONFIG_REDIS_EXPIRE_DAYS)
        password_display = "XXXXXX" if password != None else None

        print_info(
            f'Cache enabled, connecting to redis instance {host}:{port}:{db}, ssl={ssl}, password={password_display}'
        )

        return DataCache(
            RedisBackend(
                redis.Redis(
                host=host,
                port=port,
                db=db,
                password=password,
                ssl=ssl
            ), expire_days)
        )

    print_info('Cache disabled')

    return None
