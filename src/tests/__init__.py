from datetime import timedelta
import json
from redis import RedisError
from requests import Session, RequestException


from newrelic_logging import \
    CacheException, \
    DataFormat, \
    LoginException, \
    NewRelicApiException, \
    SalesforceApiException
from newrelic_logging.api import Api
from newrelic_logging.auth import Authenticator
from newrelic_logging.cache import BackendFactory, DataCache
from newrelic_logging.config import Config
from newrelic_logging.factory import Factory
from newrelic_logging.instance import Instance
from newrelic_logging.integration import Integration
from newrelic_logging.newrelic import NewRelic
from newrelic_logging.pipeline import Pipeline
from newrelic_logging.query import Query
from newrelic_logging.telemetry import Telemetry


class ApiStub:
    def __init__(
        self,
        authenticator: Authenticator = None,
        api_ver: str = None,
        query_result: dict = None,
        lines: list[str] = None,
        limits_result: dict = None,
        raise_error = False,
        raise_login_error = False,
    ):
        self.authenticator = authenticator
        self.api_ver = api_ver
        self.query_result = query_result
        self.lines = lines
        self.limits_result = limits_result
        self.soql = None
        self.query_api_ver = None
        self.limits_api_ver = None
        self.log_file_path = None
        self.chunk_size = None
        self.raise_error = raise_error
        self.raise_login_error = raise_login_error

    def authenticate(self, session: Session):
        if self.raise_login_error:
            raise LoginException()

        self.authenticator.authenticate(session)

    def query(self, session: Session, soql: str, api_ver: str = None) -> dict:
        self.soql = soql
        self.query_api_ver = api_ver

        if self.raise_error:
            raise SalesforceApiException()

        if self.raise_login_error:
            raise LoginException()

        return self.query_result

    def get_log_file(
        self,
        session: Session,
        log_file_path: str,
        chunk_size: int,
    ):
        self.log_file_path = log_file_path
        self.chunk_size = chunk_size

        if self.raise_error:
            raise SalesforceApiException()

        if self.raise_login_error:
            raise LoginException()

        yield from self.lines

    def list_limits(self, session: Session, api_ver: str = None) -> dict:
        self.limits_api_ver = api_ver

        if self.raise_error:
            raise SalesforceApiException()

        if self.raise_login_error:
            raise LoginException()

        return self.limits_result


class AuthenticatorStub:
    def __init__(
        self,
        config: Config = None,
        data_cache: DataCache = None,
        token_url: str = '',
        access_token: str = '',
        access_token_2: str = '',
        instance_url: str = '',
        grant_type: str = '',
        authenticate_called: bool = False,
        reauthenticate_called: bool = False,
        raise_login_error = False,
    ):
        self.config = config
        self.data_cache = data_cache
        self.token_url = token_url
        self.access_token = access_token
        self.access_token_2 = access_token_2
        self.instance_url = instance_url
        self.grant_type = grant_type
        self.authenticate_called = authenticate_called
        self.reauthenticate_called = reauthenticate_called
        self.raise_login_error = raise_login_error

    def get_access_token(self) -> str:
        return self.access_token

    def get_instance_url(self) -> str:
        return self.instance_url

    def get_grant_type(self) -> str:
        return self.grant_type

    def set_auth_data(self, access_token: str, instance_url: str) -> None:
        pass

    def clear_auth(self) -> None:
        pass

    def load_auth_from_cache(self) -> bool:
        return False

    def store_auth(self, auth_resp: dict) -> None:
        pass

    def authenticate_with_jwt(self, session: Session) -> None:
        pass

    def authenticate_with_password(self, session: Session) -> None:
        pass

    def authenticate(
        self,
        session: Session,
    ) -> None:
        self.authenticate_called = True
        if self.raise_login_error:
            raise LoginException('Unauthorized')

    def reauthenticate(
        self,
        session: Session,
    ) -> None:
        self.reauthenticate_called = True
        if self.raise_login_error:
            raise LoginException('Unauthorized')

        self.access_token = self.access_token_2


class DataCacheStub:
    def __init__(
        self,
        config: Config = None,
        cached_logs = {},
        cached_records = [],
        skip_record_ids = [],
    ):
        self.config = config
        self.cached_logs = cached_logs
        self.cached_records = cached_records
        self.skip_record_ids = skip_record_ids
        self.flush_called = False

    def can_skip_downloading_logfile(self, record_id: str) -> bool:
        return record_id in self.skip_record_ids

    def check_or_set_log_line(self, record_id: str, row: dict) -> bool:
        return record_id in self.cached_logs and \
            row['REQUEST_ID'] in self.cached_logs[record_id]

    def check_or_set_record_id(self, record_id: str) -> bool:
        return record_id in self.cached_records

    def flush(self) -> None:
        self.flush_called = True


class NewRelicStub:
    def __init__(self, config: Config = None, raise_error: bool = False):
        self.config = config
        self.logs = []
        self.events = []
        self.raise_error = raise_error

    def post_logs(self, session: Session, data: list[dict]) -> None:
        if self.raise_error:
            raise NewRelicApiException()

        self.logs.append(data)

    def post_events(self, session: Session, events: list[dict]) -> None:
        if self.raise_error:
            raise NewRelicApiException()

        self.events.append(events)


class QueryStub:
    def __init__(
        self,
        api: Api = None,
        query: str = '',
        config: Config = Config({}),
        api_ver: str = None,
        result: dict = { 'records': [] },
        wrapped: Query = None,
        raise_login_error: bool = False,
        raise_error: bool = False,
    ):
        self.api = api
        self.query = query
        self.config = config
        self.api_ver = api_ver
        self.executed = False
        self.raise_login_error = raise_login_error
        self.raise_error = raise_error
        self.wrapped = None
        if 'results' in config:
            self.result = { 'records': config['results'] }
        elif wrapped:
            self.wrapped = wrapped
        else:
            self.result = result

    def get(self, key: str, default = None):
        if self.wrapped:
            return self.wrapped.get(key, default)

        return self.config.get(key, default)

    def get_config(self):
        if self.wrapped:
            return self.wrapped.get_config()

        return self.config

    def execute(self, session: Session = None):
        if self.raise_error:
            raise SalesforceApiException()

        if self.raise_login_error:
            raise LoginException()

        self.executed = True

        if self.wrapped:
            return self.wrapped.execute(session)

        return self.result


class QueryFactoryStub:
    def __init__(self, query: QueryStub = None, wrap=False ):
        self.query = query
        self.queries = [] if not query else None
        self.wrap = wrap

    def new(
        self,
        api: Api,
        q: dict,
        time_lag_minutes: int = 0,
        last_to_timestamp: str = '',
        generation_interval: str = '',
    ) -> Query:
        if self.query:
            return self.query

        if self.wrap:
            qq = QueryStub(
                wrapped=Query(api, q['query'], q)
            )
        else:
            qq = QueryStub(api, q['query'], q)

        self.queries.append(qq)
        return qq


class PipelineStub:
    def __init__(
        self,
        config: Config = Config({}),
        data_cache: DataCache = None,
        new_relic: NewRelic = None,
        data_format: DataFormat = DataFormat.LOGS,
        labels: dict = {},
        numeric_fields_list: set = set(),
        raise_error: bool = False,
        raise_login_error: bool = False,
        raise_newrelic_error: bool = False,
    ):
        self.config = config
        self.data_cache = data_cache
        self.new_relic = new_relic
        self.data_format = data_format
        self.labels = labels
        self.numeric_fields_list = numeric_fields_list
        self.queries = []
        self.executed = False
        self.raise_error = raise_error
        self.raise_login_error = raise_login_error
        self.raise_newrelic_error = raise_newrelic_error

    def execute(
        self,
        session: Session,
    ):
        if self.raise_error:
            raise SalesforceApiException()

        if self.raise_login_error:
            raise LoginException()

        if self.raise_newrelic_error:
            raise NewRelicApiException()

        self.executed = True


class RedisStub:
    def __init__(self, test_cache, raise_error = False):
        self.expiry = {}
        self.test_cache = test_cache
        self.raise_error = raise_error

    def exists(self, key):
        if self.raise_error:
            raise RedisError('raise_error set')

        return key in self.test_cache

    def set(self, key, item):
        if self.raise_error:
            raise RedisError('raise_error set')

        self.test_cache[key] = item

    def smembers(self, key):
        if self.raise_error:
            raise RedisError('raise_error set')

        if not key in self.test_cache:
            return set()

        if not type(self.test_cache[key]) is set:
            raise RedisError(f'{key} is not a set')

        return self.test_cache[key]

    def sadd(self, key, *values):
        if self.raise_error:
            raise RedisError('raise_error set')

        if key in self.test_cache and not type(self.test_cache[key]) is set:
            raise RedisError(f'{key} is not a set')

        if not key in self.test_cache:
            self.test_cache[key] = set()

        for v in values:
            self.test_cache[key].add(v)

    def expire(self, key, time):
        if self.raise_error:
            raise RedisError('raise_error set')

        self.expiry[key] = time


class BackendStub:
    def __init__(self, test_cache, raise_error = False):
        self.redis = RedisStub(test_cache, raise_error)

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


class BackendFactoryStub:
    def __init__(self, raise_error = False):
        self.raise_error = raise_error

    def new_backend(self, config: Config):
        if self.raise_error:
            raise CacheException('raise_error set')

        return BackendStub({})


class MultiRequestSessionStub:
    def __init__(self, responses=[], raise_error=False):
        self.raise_error = raise_error
        self.requests = []
        self.responses = responses
        self.count = 0

    def get(self, *args, **kwargs):
        self.requests.append({
            'url': args[0],
            'headers': kwargs['headers'],
            'stream': kwargs['stream'] if 'stream' in kwargs else None,
        })

        if self.raise_error:
            raise RequestException('raise_error set')

        if self.count < len(self.responses):
            self.count += 1

        return self.responses[self.count - 1]


class ResponseStub:
    def __init__(self, status_code, reason, text, lines, encoding=None):
        self.status_code = status_code
        self.reason = reason
        self.text = text
        self.lines = lines
        self.chunk_size = None
        self.decode_unicode = None
        self.encoding = encoding
        self.iter_lines_called = False

    def iter_lines(self, *args, **kwargs):
        self.iter_lines_called = True

        if 'chunk_size' in kwargs:
            self.chunk_size = kwargs['chunk_size']

        if 'decode_unicode' in kwargs:
            self.decode_unicode = kwargs['decode_unicode']

        yield from self.lines

    def json(self, *args, **kwargs):
        return json.loads(self.text)


class InstanceStub:
    def __init__(
        self,
        instance_name: str = '',
        config: Config = Config({}),
        api: Api = None,
        pipeline: Pipeline = None,
        queries: list[dict] = None,
        raise_login_error: bool = False,
        raise_error: bool = False,
        raise_newrelic_error: bool = False,
        raise_cache_error: bool = False,
        raise_unexpected_error: bool = False,
    ):
        self.name = instance_name
        self.config = config
        self.api = api
        self.pipeline = pipeline
        self.queries = queries
        self.harvest_called = False
        self.raise_login_error = raise_login_error
        self.raise_error = raise_error
        self.raise_newrelic_error = raise_newrelic_error
        self.raise_cache_error = raise_cache_error
        self.raise_unexpected_error = raise_unexpected_error

    def harvest(self, session: Session):
        if self.raise_error:
            raise SalesforceApiException()

        if self.raise_login_error:
            raise LoginException()

        if self.raise_newrelic_error:
            raise NewRelicApiException()

        if self.raise_cache_error:
            raise CacheException()

        if self.raise_unexpected_error:
            raise Exception()

        self.harvest_called = True


class IntegrationStub:
    def __init__(
        self,
        config: Config = Config({}),
        event_type_fields_mapping: dict = {},
        numeric_fields_list: set = set(),
        initial_delay: int = 0,
    ):
        pass

class ReceiverStub:
    def __init__(
        self,
        raise_login_error: bool = False,
        raise_error: bool = False,
        logs: list[dict] = [],
    ):
        self.executed = False
        self.raise_login_error = raise_login_error
        self.raise_error = raise_error
        self.logs = logs

    def execute(
        self,
        session: Session,
    ):
        if self.raise_error:
            raise SalesforceApiException()

        if self.raise_login_error:
            raise LoginException()

        self.executed = True

        yield from self.logs


class SessionStub:
    def __init__(self, raise_error=False, raise_connection_error=False):
        self.raise_error = raise_error
        self.raise_connection_error = raise_connection_error
        self.response = None
        self.headers = None
        self.url = None
        self.stream = None

    def get(self, *args, **kwargs):
        self.url = args[0]
        self.headers = kwargs['headers']
        if 'stream' in kwargs:
            self.stream = kwargs['stream']

        if self.raise_connection_error:
            raise ConnectionError('raise_connection_error set')

        if self.raise_error:
            raise RequestException('raise_error set')

        return self.response


class TelemetryStub:
    def __init__(
        self,
        integration_name: str = 'test_instance',
        new_relic: NewRelic = None,
        empty: bool = True
    ):
        self.integration_name = integration_name
        self.new_relic = new_relic
        self.empty = empty
        self.flush_called = False

    def is_empty(self):
        return self.empty

    def log_info(self, msg: str):
        self.record_log(msg, "info")

    def log_err(self, msg: str):
        self.record_log(msg, "error")

    def log_warn(self, msg: str):
        self.record_log(msg, "warn")

    def record_log(self, msg: str, level: str):
        pass

    def clear(self):
        pass

    def flush(self, session: Session):
        self.flush_called = True


class FactoryStub:
    def __init__(
        self,
        f: Factory,
        backend_factory: BackendFactoryStub = None,
        data_cache: DataCacheStub = None,
        authenticator: AuthenticatorStub = None,
        api: ApiStub = None,
        pipeline: PipelineStub = None,
        instance: InstanceStub = None,
        integration: IntegrationStub = None,
        new_relic: NewRelicStub = None,
        telemetry: TelemetryStub = None
    ):
        self.f = f
        self.backend_factory = backend_factory
        self.data_cache = data_cache
        self.authenticator = authenticator
        self.api = api
        self.pipeline = pipeline
        self.instance = instance
        self.integration = integration
        self.new_relic = new_relic
        self.telemetry = telemetry

    def new_backend_factory(self):
        if self.backend_factory:
            return self.backend_factory

        return self.f.new_backend_factory()

    def new_data_cache(
        self,
        instance_config: Config,
        backend_factory: BackendFactory,
    ) -> DataCache:
        if self.data_cache:
            return self.data_cache

        return self.f.new_data_cache(instance_config, backend_factory)

    def new_authenticator(
        self,
        instance_config: Config,
        data_cache: DataCache,
    ) -> Authenticator:
        if self.authenticator:
            return self.authenticator

        return self.f.new_authenticator(instance_config, data_cache)

    def new_api(self, authenticator: Authenticator, api_ver: str):
        if self.api:
            return self.api

        return self.f.new_api(authenticator, api_ver)

    def new_pipeline(
        self,
        config: Config,
        data_cache: DataCache,
        new_relic: NewRelic,
        data_format: DataFormat,
        labels: dict,
        numeric_fields_list: set,
    ) -> Pipeline:
        if self.pipeline:
            return self.pipeline

        return self.f.new_pipeline(
            config,
            data_cache,
            new_relic,
            data_format,
            labels,
            numeric_fields_list,
        )

    def new_instance(
        self,
        factory,
        instance_name: str,
        instance_config: Config,
        data_format: DataFormat,
        new_relic: NewRelic,
        receivers: list[callable],
        labels: dict,
        numeric_fields_list: set = set(),
    ) -> Instance:
        if self.instance:
            return self.instance

        return self.f.new_instance(
            factory,
            instance_name,
            instance_config,
            data_format,
            new_relic,
            receivers,
            labels,
            numeric_fields_list,
        )

    def new_integration(
        self,
        factory,
        config: Config,
        receivers: list[callable],
        numeric_fields_list: set = set(),
    ) -> Integration:
        if self.integration:
            return self.integration

        return self.f.new_integration(
            factory,
            config,
            receivers,
            numeric_fields_list,
        )

    def new_new_relic(self, config: Config):
        if self.new_relic:
            return self.new_relic

        return self.f.new_new_relic(config)

    def new_telemetry(
        self,
        config: Config,
        new_relic: NewRelic,
    ):
        if self.telemetry:
            return self.telemetry

        return self.f.new_telemetry(config, new_relic)
