from datetime import datetime, timedelta
from requests import Session

from .api import ApiFactory
from .auth import Authenticator
from .cache import DataCache
from . import config as mod_config
from .pipeline import Pipeline
from . import query as mod_query
from .telemetry import print_info, print_warn
from .util import get_iso_date_with_offset


CSV_SLICE_SIZE = 1000
SALESFORCE_CREATED_DATE_QUERY = \
    "SELECT Id,EventType,CreatedDate,LogDate,Interval,LogFile,Sequence From EventLogFile Where CreatedDate>={" \
    "from_timestamp} AND CreatedDate<{to_timestamp} AND Interval='{log_interval_type}'"
SALESFORCE_LOG_DATE_QUERY = \
    "SELECT Id,EventType,CreatedDate,LogDate,Interval,LogFile,Sequence From EventLogFile Where LogDate>={" \
    "from_timestamp} AND LogDate<{to_timestamp} AND Interval='{log_interval_type}'"


class SalesForce:
    def __init__(
        self,
        instance_name: str,
        config: mod_config.Config,
        data_cache: DataCache,
        authenticator: Authenticator,
        pipeline: Pipeline,
        api_factory: ApiFactory,
        query_factory: mod_query.QueryFactory,
        initial_delay: int,
        queries: list[dict] = None,
    ):
        self.instance_name = instance_name
        self.data_cache = data_cache
        self.pipeline = pipeline
        self.query_factory = query_factory
        self.time_lag_minutes = config.get(
            mod_config.CONFIG_TIME_LAG_MINUTES,
            mod_config.DEFAULT_TIME_LAG_MINUTES if not self.data_cache else 0,
        )
        self.date_field = config.get(
            mod_config.CONFIG_DATE_FIELD,
            mod_config.DATE_FIELD_LOG_DATE if not self.data_cache \
                else mod_config.DATE_FIELD_CREATE_DATE,
        )
        self.generation_interval = config.get(
            mod_config.CONFIG_GENERATION_INTERVAL,
            mod_config.DEFAULT_GENERATION_INTERVAL,
        )
        self.last_to_timestamp = get_iso_date_with_offset(
            self.time_lag_minutes,
            initial_delay,
        )
        self.api = api_factory.new(
            authenticator,
            config.get('api_ver', '52.0'),
        )
        self.queries = queries if queries else \
            [{
                'query': SALESFORCE_LOG_DATE_QUERY \
                    if self.date_field.lower() == 'logdate' \
                    else SALESFORCE_CREATED_DATE_QUERY
            }]

    def authenticate(self, sfdc_session: Session):
        self.api.authenticate(sfdc_session)

    def slide_time_range(self):
        self.last_to_timestamp = get_iso_date_with_offset(
            self.time_lag_minutes
        )

    # NOTE: Is it possible that different SF orgs have overlapping IDs? If this is possible, we should use a different
    #       database for each org, or add a prefix to keys to avoid conflicts.

    def fetch_logs(self, session: Session) -> list[dict]:
        print_info(f"Queries = {self.queries}")

        for q in self.queries:
            query = self.query_factory.new(
                self.api,
                q,
                self.time_lag_minutes,
                self.last_to_timestamp,
                self.generation_interval,
            )

            response = query.execute(session)

            if not response or not 'records' in response:
                print_warn(f'no records returned for query {query.query}')
                continue

            self.pipeline.execute(
                self.api,
                session,
                query,
                response['records'],
            )

        self.slide_time_range()


class SalesForceFactory:
    def __init__(self):
        pass

    def new(
        self,
        instance_name: str,
        config: mod_config.Config,
        data_cache: DataCache,
        authenticator: Authenticator,
        pipeline: Pipeline,
        query_factory: mod_query.QueryFactory,
        initial_delay: int,
        queries: list[dict] = None,
    ):
        return SalesForce(
            instance_name,
            config,
            data_cache,
            authenticator,
            pipeline,
            query_factory,
            initial_delay,
            queries,
        )
