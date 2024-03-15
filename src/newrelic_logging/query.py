import copy
from datetime import datetime, timedelta
from requests import RequestException, Session

from . import SalesforceApiException
from .config import Config
from .telemetry import print_info
from .util import get_iso_date_with_offset, substitute

class Query:
    def __init__(
        self,
        query: str,
        config: Config,
        api_ver: str,
    ):
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
        instance_url: str,
        access_token: str,
    ):
        url = f'{instance_url}/services/data/v{self.api_ver}/query?q={self.query}'

        try:
            print_info(f'Running query {self.query} using url {url}')

            query_response = session.get(url, headers={
                'Authorization': f'Bearer {access_token}'
            })
            if query_response.status_code != 200:
                raise SalesforceApiException(
                    query_response.status_code,
                    f'error when trying to run SOQL query. ' \
                    f'status-code:{query_response.status_code}, ' \
                    f'reason: {query_response.reason} ' \
                    f'response: {query_response.text} '
                )

            return query_response.json()
        except RequestException as e:
            raise SalesforceApiException(
                -1,
                f'error when trying to run SOQL query. cause: {e}',
            ) from e


class QueryFactory:
    def __init__(self):
        pass

    def new(
        self,
        q: dict,
        time_lag_minutes: int,
        last_to_timestamp: str,
        generation_interval: str,
        default_api_ver: str,
    ) -> Query:
        to_timestamp = get_iso_date_with_offset(time_lag_minutes)
        from_timestamp = last_to_timestamp

        qp = copy.deepcopy(q)
        qq = qp.pop('query', '')

        args = {
            'to_timestamp': to_timestamp,
            'from_timestamp': from_timestamp,
            'log_interval_type': generation_interval,
        }

        env = qp['env'] if 'env' in qp and type(qp['env']) is dict else {}

        return Query(
            substitute(args, qq, env).replace(' ', '+'),
            Config(qp),
            qp.get('api_ver', default_api_ver)
        )
