import copy
from requests import RequestException, Session

from . import SalesforceApiException
from .api import Api
from .config import Config
from .telemetry import print_info
from .util import get_iso_date_with_offset, substitute

class Query:
    def __init__(
        self,
        api: Api,
        query: str,
        config: Config,
        api_ver: str = None,
    ):
        self.api = api
        self.query = query
        self.config = config
        self.api_ver = api_ver

    def get(self, key: str, default = None):
        return self.config.get(key, default)

    def get_config(self):
        return self.config

    def execute(
        self,
        session: Session,
    ):
        print_info(f'Running query {self.query}...')
        return self.api.query(session, self.query, self.api_ver)


class QueryFactory:
    def __init__(self):
        pass

    def build_args(
        self,
        time_lag_minutes: int,
        last_to_timestamp: str,
        generation_interval: str,
    ):
        return {
            'to_timestamp': get_iso_date_with_offset(time_lag_minutes),
            'from_timestamp': last_to_timestamp,
            'log_interval_type': generation_interval,
        }

    def get_env(self, q: dict) -> dict:
        if 'env' in q and type(q['env']) is dict:
            return q['env']

        return {}

    def new(
        self,
        api: Api,
        q: dict,
        time_lag_minutes: int,
        last_to_timestamp: str,
        generation_interval: str,
    ) -> Query:
        qp = copy.deepcopy(q)
        qq = qp.pop('query', '')

        return Query(
            api,
            substitute(
                self.build_args(
                    time_lag_minutes,
                    last_to_timestamp,
                    generation_interval,
                ),
                qq,
                self.get_env(qp),
            ).replace(' ', '+'),
            Config(qp),
            qp.get('api_ver', None)
        )
