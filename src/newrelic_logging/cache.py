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


# Going through this function makes testing easier
def redis_connect(**kwargs) -> redis.Redis: # pragma: no cover
    return redis.Redis(**kwargs)


class RedisBackend:
    def __init__(self, redis):
        self.redis = redis

    def exists(self, key):
        return self.redis.exists(key)

    def put(self, key, item):
        self.redis.set(key, item)

    def get_set(self, key):
        return self.redis.smembers(key)

    def set_add(self, key, *values):
        self.redis.sadd(key, *values)

    def set_expiry(self, key, days):
        self.redis.expire(key, timedelta(days=days))


class BackendFactory:
    def __init__(self):
        pass

    def new_backend(
        self,
        config: Config,
        redis_connector: callable = redis_connect, # makes testing easier
    ):
        host = config.get(CONFIG_REDIS_HOST, DEFAULT_REDIS_HOST)
        port = config.get_int(CONFIG_REDIS_PORT, DEFAULT_REDIS_PORT)
        db = config.get_int(CONFIG_REDIS_DB_NUMBER, DEFAULT_REDIS_DB_NUMBER)
        password = config.get(CONFIG_REDIS_PASSWORD)
        ssl = config.get_bool(CONFIG_REDIS_USE_SSL, DEFAULT_REDIS_SSL)
        password_display = "XXXXXX" if password != None else None

        print_info(
            f'connecting to redis instance {host}:{port}:{db}, ssl={ssl}, password={password_display}'
        )

        return RedisBackend(
            redis_connector(
                host=host,
                port=port,
                db=db,
                password=password,
                ssl=ssl,
                decode_responses=True,
            ),
        )


class BufferedAddSetCache:
    def __init__(self, s: set):
        self.s = s
        self.buffer = set()

    def check_or_set(self, item: str) -> bool:
        if item in self.s or item in self.buffer:
            return True

        self.buffer.add(item)

        return False

    def get_buffer(self) -> set:
        return self.buffer


class DataCache:
    def __init__(self, backend, expiry):
        self.backend = backend
        self.expiry = expiry
        self.log_records = {}
        self.query_records = None

    def can_skip_downloading_logfile(self, record_id: str) -> bool:
        try:
            return self.backend.exists(record_id)
        except Exception as e:
            raise CacheException(f'failed checking record {record_id}: {e}')

    def check_or_set_log_line(self, record_id: str, line: dict) -> bool:
        try:
            if not record_id in self.log_records:
                self.log_records[record_id] = BufferedAddSetCache(
                    self.backend.get_set(record_id),
                )

            return self.log_records[record_id].check_or_set(line['REQUEST_ID'])
        except Exception as e:
            raise CacheException(f'failed checking record {record_id}: {e}')

    def check_or_set_record_id(self, record_id: str) -> bool:
        try:
            if not self.query_records:
                self.query_records = BufferedAddSetCache(
                    self.backend.get_set('record_ids'),
                )

            return self.query_records.check_or_set(record_id)
        except Exception as e:
            raise CacheException(f'failed checking record {record_id}: {e}')

    def flush(self) -> None:
        try:
            for record_id in self.log_records:
                buf = self.log_records[record_id].get_buffer()
                if len(buf) > 0:
                    self.backend.set_add(record_id, *buf)

                self.backend.set_expiry(record_id, self.expiry)

            if self.query_records:
                buf = self.query_records.get_buffer()
                if len(buf) > 0:
                    for id in buf:
                        self.backend.put(id, 1)
                        self.backend.set_expiry(id, self.expiry)

                    self.backend.set_add('record_ids', *buf)
                    self.backend.set_expiry('record_ids', self.expiry)

            # attempt to reclaim memory
            for record_id in self.log_records:
                self.log_records[record_id] = None

            self.log_records = {}
            self.query_records = None

            gc.collect()
        except Exception as e:
            raise CacheException(f'failed flushing cache: {e}')
